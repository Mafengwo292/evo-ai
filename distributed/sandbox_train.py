"""
distributed/sandbox_train.py
----------------------------
在当前沙箱里实际训练一个 nanoGPT。

这是分布式自进化大模型的**第一个节点**。
模型权重从这里开始初始化，并真实地在训练中变化。

CPU + 2 线程的极简训练。
"""

import sys
import os
import time
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW

sys.path.insert(0, "/workspace/evo-ai")

# 内置莎士比亚风格文本（避免外网依赖）
SHAKESPEARE_TEXT = """ROMEO:
But, soft! what light through yonder window breaks?
It is the east, and Juliet is the sun.
Arise, fair sun, and kill the envious moon,
Who is already sick and pale with grief,
That thou her maid art far more fair than she.

JULIET:
O Romeo, Romeo! wherefore art thou Romeo?
Deny thy father, and refuse thy name;
Or, if thou wilt not, be but sworn my love,
And I'll no longer be a Capulet.

ROMEO:
I take thee at thy word:
Call me but love, and I'll be new baptized;
Henceforth I never will be Romeo.

JULIET:
What man art thou that thus bescreen'd in night
So stumblest on my counsel?

ROMEO:
By a name I know not how to tell thee who I am:
My name, dear saint, is hateful to myself,
Because it is an enemy to thee.

HAMLET:
To be, or not to be, that is the question:
Whether 'tis nobler in the mind to suffer
The slings and arrows of outrageous fortune,
Or to take arms against a sea of troubles,
And by opposing end them.

OPHELIA:
O, what a noble mind is here o'erthrown!
The courtier's, soldier's, scholar's, eye, tongue, sword.

KING RICHARD III:
Now is the winter of our discontent
Made glorious summer by this sun of York;
And all the clouds that lour'd upon our house
In the deep bosom of the ocean buried.

LADY MACBETH:
Out, damned spot! out, I say! One; two;
Why, then, 'tis time to do't. Hell is murky.
Fie, my lord, fie! a soldier, and afeard?

MACBETH:
I have no words,
My voice is in my sword, thou bloodier villain
Than terms can give thee out.

PROSPERO:
Our revels now are ended. These our actors,
As I foretold you, were all spirits and
Are melted into air, into thin air.

""" * 5  # 重复几次增加数据量


# ==========================================================
# Inline 一个超简化的 nanoGPT（避免外部依赖）
# ==========================================================

class TinyGPT(nn.Module):
    """超简化的 GPT：1 个 transformer block"""

    def __init__(self, vocab_size, d_model=64, n_head=2, block_size=32):
        super().__init__()
        self.block_size = block_size
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(block_size, d_model)
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = nn.MultiheadAttention(d_model, n_head, batch_first=True)
        self.ln2 = nn.LayerNorm(d_model)
        self.mlp = nn.Sequential(
            nn.Linear(d_model, 4 * d_model),
            nn.GELU(),
            nn.Linear(4 * d_model, d_model),
        )
        self.head = nn.Linear(d_model, vocab_size)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.tok_emb(idx) + self.pos_emb(pos)
        # causal mask
        mask = torch.triu(torch.ones(T, T, device=idx.device) * float('-inf'), diagonal=1)
        h = self.ln1(x)
        h, _ = self.attn(h, h, h, attn_mask=mask, is_causal=True, need_weights=False)
        x = x + h
        x = x + self.mlp(self.ln2(x))
        logits = self.head(x)
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens=100, temperature=1.0):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, idx_next], dim=1)
        return idx


class CharTokenizer:
    def __init__(self, text):
        chars = sorted(set(text))
        self.vocab_size = len(chars)
        self.stoi = {c: i for i, c in enumerate(chars)}
        self.itos = {i: c for i, c in enumerate(chars)}
    def encode(self, s):
        return [self.stoi[c] for c in s if c in self.stoi]
    def decode(self, ids):
        return "".join(self.itos[i] for i in ids)


def train_sandbox_node(node_id="sandbox-0", steps=200, batch_size=8, block_size=32, d_model=64):
    """
    在沙箱里真的训练。
    返回训练好的 model + 训练历史。
    """
    print(f"\n{'='*60}")
    print(f"  [Node: {node_id}] 开始训练")
    print(f"{'='*60}")

    device = "cpu"
    torch.manual_seed(42)

    # 1) 数据
    text = SHAKESPEARE_TEXT
    tok = CharTokenizer(text)
    data = torch.tensor(tok.encode(text), dtype=torch.long)
    print(f"  · 数据: {len(data)} tokens, vocab={tok.vocab_size}")

    # 2) 模型
    model = TinyGPT(vocab_size=tok.vocab_size, d_model=d_model, n_head=2, block_size=block_size).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  · 模型: {n_params:,} 参数 ({n_params/1e3:.1f}K)")

    # 3) 优化器
    optimizer = AdamW(model.parameters(), lr=3e-3)

    # 4) 训练
    print(f"  · 训练 {steps} 步，batch_size={batch_size}, block_size={block_size}")
    print(f"  · device: {device}")
    print()
    history = []

    model.train()
    t0 = time.time()
    for step in range(steps):
        # 随机采样 batch
        ix = torch.randint(0, len(data) - block_size - 1, (batch_size,))
        x = torch.stack([data[i:i+block_size] for i in ix])
        y = torch.stack([data[i+1:i+block_size+1] for i in ix])

        logits, loss = model(x, y)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step % 20 == 0 or step == steps - 1:
            elapsed = time.time() - t0
            history.append((step, loss.item()))
            print(f"    step {step:4d} | loss {loss.item():.4f} | {elapsed:.1f}s")

    # 5) 保存
    save_path = f"checkpoints/{node_id}.pt"
    os.makedirs("checkpoints", exist_ok=True)
    torch.save({
        "model": model.state_dict(),
        "config": {"vocab_size": tok.vocab_size, "d_model": d_model, "block_size": block_size},
        "tokenizer_chars": list(tok.stoi.keys()),
        "history": history,
        "node_id": node_id,
        "n_params": n_params,
    }, save_path)
    print(f"\n  ✓ 训练完成。权重保存到 {save_path}")
    print(f"  ✓ 训练耗时: {time.time()-t0:.1f}s")
    print(f"  ✓ 最终 loss: {history[-1][1]:.4f}")

    return model, tok, history, save_path


def generate_from_checkpoint(ckpt_path, prompt="ROMEO:\n", max_tokens=200, temperature=0.7):
    """从 checkpoint 生成文本"""
    ckpt = torch.load(ckpt_path, weights_only=False)
    tok = CharTokenizer("".join(ckpt["tokenizer_chars"]))
    # 注意：这里 vocab_size 用了 .vocab_size 但 stoi 是 dict
    # 重新构造：把 char 列表按 stoi 顺序排
    chars = ckpt["tokenizer_chars"]
    tok.stoi = {c: i for i, c in enumerate(chars)}
    tok.itos = {i: c for i, c in enumerate(chars)}
    tok.vocab_size = len(chars)

    model = TinyGPT(
        vocab_size=ckpt["config"]["vocab_size"],
        d_model=ckpt["config"]["d_model"],
        n_head=2,
        block_size=ckpt["config"]["block_size"],
    )
    model.load_state_dict(ckpt["model"])
    model.eval()

    ids = tok.encode(prompt)
    if not ids:
        ids = [0]
    x = torch.tensor([ids], dtype=torch.long)
    out = model.generate(x, max_new_tokens=max_tokens, temperature=temperature)
    text = tok.decode(out[0].tolist())
    return text


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--node_id", default="sandbox-0")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--d_model", type=int, default=64)
    parser.add_argument("--block_size", type=int, default=32)
    args = parser.parse_args()

    model, tok, history, path = train_sandbox_node(
        node_id=args.node_id,
        steps=args.steps,
        batch_size=args.batch,
        d_model=args.d_model,
        block_size=args.block_size,
    )

    print(f"\n{'='*60}")
    print(f"  生成测试")
    print(f"{'='*60}")
    text = generate_from_checkpoint(path, prompt="ROMEO:\n", max_tokens=150, temperature=0.7)
    print(text)
