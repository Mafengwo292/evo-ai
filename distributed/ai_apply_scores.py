"""
distributed/ai_apply_scores.py
------------------------------
把 AI 评估者的评分应用到样本上，并基于评分继续训练。
"""

import os
import sys
import json
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW

sys.path.insert(0, "/workspace/evo-ai")

from distributed.sandbox_train import (
    TinyGPT, CharTokenizer, SHAKESPEARE_TEXT, train_sandbox_node
)


# Mavis 作为 AI 评估者的真实评分（基于刚才生成的样本）
AI_SCORES = {
    0: 0.30,   # ROMEO
    1: 0.20,   # JULIET
    2: 0.10,   # HAMLET
    3: 0.45,   # KING RICHARD III
    4: 0.35,   # MACBETH
}


def apply_ai_scores(pending_path="data/pending_evaluations.jsonl",
                    output_path="data/ai_evaluations.jsonl"):
    """把 Mavis 的评分写入文件"""
    if not os.path.exists(pending_path):
        print(f"[AI Scores] No pending file at {pending_path}")
        return []

    samples = []
    with open(pending_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            sid = d.get("id")
            if sid in AI_SCORES:
                d["ai_score"] = AI_SCORES[sid]
                d["ai_evaluator"] = "Mavis (root session)"
            samples.append(d)

    # 写最终评估
    with open(output_path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"[AI Scores] Applied Mavis's scores to {len(samples)} samples")
    for s in samples:
        print(f"  Sample {s['id']}: {s.get('ai_score', '?')}")
    return samples


def augment_training_data(samples, base_text, threshold=0.30):
    """把 AI 评分 ≥ threshold 的样本加入训练集"""
    extra_text = ""
    approved = [s for s in samples if s.get("ai_score", 0) >= threshold]
    for s in approved:
        extra_text += s.get("text", "") + "\n\n"
        print(f"  [Approved] Sample {s['id']} (score={s['ai_score']}) added to training set")

    augmented = base_text + "\n" + extra_text
    aug_path = "data/augmented_train.txt"
    with open(aug_path, "w", encoding="utf-8") as f:
        f.write(augmented)
    print(f"\n  Augmented training set: {len(base_text)} -> {len(augmented)} chars")
    print(f"  Saved to {aug_path}")
    return augmented


def continue_training_with_ai_feedback(steps=200):
    """
    用 AI 评估增强后的数据继续训练。
    这是"自进化"的关键一步：AI 评估 → 数据增强 → 重新训练。
    """
    print(f"\n{'='*60}")
    print(f"  继续训练：使用 AI 评估增强数据")
    print(f"{'='*60}")

    # 用 augmented 数据训练
    aug_path = "data/augmented_train.txt"
    if not os.path.exists(aug_path):
        print(f"  No augmented data, using base text only")
        train_text = SHAKESPEARE_TEXT
    else:
        with open(aug_path, "r", encoding="utf-8") as f:
            train_text = f.read()
        print(f"  Loaded augmented data: {len(train_text)} chars")

    # 直接用 sandbox_train 里的训练流程
    device = "cpu"
    torch.manual_seed(123)   # 不同 seed，模拟新一代
    tok = CharTokenizer(train_text)
    data = torch.tensor(tok.encode(train_text), dtype=torch.long)
    print(f"  Vocab: {tok.vocab_size}, Tokens: {len(data)}")

    # 加载之前的 checkpoint 继续训练
    ckpt = torch.load("checkpoints/sandbox-0.pt", weights_only=False)
    model = TinyGPT(
        vocab_size=ckpt["config"]["vocab_size"],
        d_model=ckpt["config"]["d_model"],
        n_head=2,
        block_size=ckpt["config"]["block_size"],
    )
    # 注意：vocab 可能不一样，所以用 strict=False
    model.load_state_dict(ckpt["model"], strict=False)

    optimizer = AdamW(model.parameters(), lr=1e-3)   # 较低学习率
    block_size = ckpt["config"]["block_size"]
    batch_size = 8

    print(f"\n  在 AI 增强数据上继续训练 {steps} 步...")
    print(f"  (基于上一代 sandbox-0 的权重)")
    print()
    model.train()
    t0 = time.time()
    for step in range(steps):
        ix = torch.randint(0, len(data) - block_size - 1, (batch_size,))
        x = torch.stack([data[i:i+block_size] for i in ix])
        y = torch.stack([data[i+1:i+block_size+1] for i in ix])
        logits, loss = model(x, y)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step % 30 == 0 or step == steps - 1:
            print(f"    step {step:4d} | loss {loss.item():.4f}")

    # 保存新一代
    save_path = "checkpoints/sandbox-1.pt"
    os.makedirs("checkpoints", exist_ok=True)
    torch.save({
        "model": model.state_dict(),
        "config": ckpt["config"],
        "tokenizer_chars": list(tok.stoi.keys()),
        "parent": "sandbox-0.pt",
        "generation": 1,
        "ai_evaluator": "Mavis",
    }, save_path)
    print(f"\n  ✓ 训练完成。sandbox-1.pt 保存")
    print(f"  ✓ 父节点: sandbox-0.pt")
    print(f"  ✓ 训练者: Mavis (AI 评估反馈)")
    print(f"  ✓ 最终 loss: {loss.item():.4f}")
    return model, tok, save_path


if __name__ == "__main__":
    samples = apply_ai_scores()
    augmented = augment_training_data(samples, SHAKESPEARE_TEXT, threshold=0.30)
    model, tok, path = continue_training_with_ai_feedback(steps=200)
