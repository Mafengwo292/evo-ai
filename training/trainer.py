"""
training/trainer.py
-------------------
训练循环。W1 是单机版（CPU/GPU 都能跑）。
W2 会扩展为 DDP 分布式版本。
"""

from __future__ import annotations
import time
import math
import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW

from model.gpt import GPT, GPTConfig
from data.dataset import prepare_data


def get_lr(step: int, warmup: int, max_steps: int, max_lr: float, min_lr: float) -> float:
    """Cosine 学习率 schedule + warmup"""
    if step < warmup:
        return max_lr * (step + 1) / warmup
    if step > max_steps:
        return min_lr
    decay_ratio = (step - warmup) / (max_steps - warmup)
    coeff = 0.5 * (1.0 + math.cos(math.pi * decay_ratio))
    return min_lr + coeff * (max_lr - min_lr)


@torch.no_grad()
def estimate_loss(model, train_loader, val_loader, device, eval_iters: int = 20):
    """估算 train / val loss"""
    model.eval()
    out = {}
    for name, loader in [("train", train_loader), ("val", val_loader)]:
        losses = torch.zeros(eval_iters)
        for i, (x, y) in enumerate(loader):
            if i >= eval_iters:
                break
            x, y = x.to(device), y.to(device)
            _, loss = model(x, y)
            losses[i] = loss.item()
        out[name] = losses.mean().item()
    model.train()
    return out


def train(config: GPTConfig, max_steps: int = 2000, batch_size: int = 32,
          max_lr: float = 3e-4, min_lr: float = 3e-5, warmup: int = 100,
          eval_interval: int = 200, save_path: str = "checkpoints/gpt_w1.pt"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[Train] Device: {device}")

    # 1) 数据
    train_ds, val_ds, tok = prepare_data(block_size=config.block_size)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    # 2) 模型
    model = GPT(config).to(device)
    n_params = model.num_params()
    print(f"[Model] Params: {n_params:,} ({n_params/1e6:.2f}M)")

    # 3) 优化器
    optimizer = AdamW(model.parameters(), lr=max_lr, betas=(0.9, 0.95), weight_decay=0.1)

    # 4) 训练循环
    print(f"[Train] Starting training: {max_steps} steps, batch={batch_size}, lr={max_lr}")
    print("=" * 60)

    model.train()
    iter_train = iter(train_loader)
    t0 = time.time()
    running_loss = 0.0

    for step in range(max_steps):
        # 调整 LR
        lr = get_lr(step, warmup, max_steps, max_lr, min_lr)
        for pg in optimizer.param_groups:
            pg["lr"] = lr

        # 取 batch
        try:
            x, y = next(iter_train)
        except StopIteration:
            iter_train = iter(train_loader)
            x, y = next(iter_train)
        x, y = x.to(device), y.to(device)

        # 前向 + 反向
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        running_loss += loss.item()

        # 日志
        if step % eval_interval == 0 or step == max_steps - 1:
            t1 = time.time()
            dt = t1 - t0
            t0 = t1
            losses = estimate_loss(model, train_loader, val_loader, device)
            avg = running_loss / max(1, eval_interval)
            running_loss = 0.0
            print(f"step {step:5d} | lr {lr:.2e} | "
                  f"train loss {losses['train']:.4f} | val loss {losses['val']:.4f} | "
                  f"avg {avg:.4f} | {dt:.1f}s")

    # 5) 保存
    os = __import__("os")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save({
        "model": model.state_dict(),
        "config": config.__dict__,
        "tokenizer": {"vocab_size": tok.vocab_size},  # 简化保存
    }, save_path)
    print(f"\n[Save] Model saved to {save_path}")
    return model, tok
