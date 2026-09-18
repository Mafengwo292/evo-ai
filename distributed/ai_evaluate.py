"""
distributed/ai_evaluate.py
---------------------------
AI 评估者接口。

让我（这个对话中的 Mavis）作为评估者，给生成的样本打分。
这是"AI 助理作为分布式自进化系统的一部分"的具体实现。
"""

import os
import sys
import json
import time
from typing import List, Dict

sys.path.insert(0, "/workspace/evo-ai")

from distributed.sandbox_train import generate_from_checkpoint, train_sandbox_node, SHAKESPEARE_TEXT


def generate_samples(ckpt_path: str, n: int = 5, prompts: List[str] = None,
                     max_tokens: int = 100) -> List[Dict]:
    """从 checkpoint 生成 N 个样本"""
    prompts = prompts or ["ROMEO:\n", "JULIET:\n", "HAMLET:\n", "KING RICHARD III:\n", "MACBETH:\n"]
    samples = []
    for i, prompt in enumerate(prompts[:n]):
        text = generate_from_checkpoint(ckpt_path, prompt=prompt, max_tokens=max_tokens, temperature=0.8)
        samples.append({"id": i, "prompt": prompt.strip(), "text": text, "ai_score": None})
    return samples


def save_evaluations(samples: List[Dict], path: str = "data/ai_evaluations.jsonl"):
    """保存 AI 评估结果"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"[AI Evaluator] Saved {len(samples)} evaluations to {path}")


def continue_training_from_buffer(ckpt_path: str, steps: int = 200):
    """
    从 AI 评估过的 buffer 继续训练。
    这一步把"我评估过的样本"当作额外训练数据，加到原数据上。
    """
    # 读 AI 评估的样本
    eval_path = "data/ai_evaluations.jsonl"
    extra_text = ""
    if os.path.exists(eval_path):
        with open(eval_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                if d.get("ai_score", 0) >= 0.7:   # 只用高分样本
                    extra_text += d.get("text", "") + "\n"
        print(f"[Continue Training] Loaded {len(extra_text)} chars of AI-approved text")

    # 把高分样本加入训练数据
    augmented_text = SHAKESPEARE_TEXT + "\n" + extra_text
    with open("data/augmented_train.txt", "w", encoding="utf-8") as f:
        f.write(augmented_text)

    print(f"[Continue Training] Augmented data size: {len(augmented_text)} chars")
    print(f"[Continue Training] (下一步：用 augmented_train.txt 重新训练)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", default="checkpoints/sandbox-0.pt")
    parser.add_argument("--n_samples", type=int, default=5)
    parser.add_argument("--max_tokens", type=int, default=100)
    args = parser.parse_args()

    print("=" * 60)
    print("  AI 评估者：让 Mavis 评估生成的样本")
    print("=" * 60)
    print(f"  Checkpoint: {args.ckpt}")
    print(f"  生成 {args.n_samples} 个样本，等待 AI 评估...\n")

    samples = generate_samples(args.ckpt, n=args.n_samples, max_tokens=args.max_tokens)

    for s in samples:
        print(f"\n--- Sample {s['id']} (prompt: {s['prompt']!r}) ---")
        print(s["text"])
        print(f"[等待 AI 评分]")

    # 保存未评分的样本，让 AI 在对话中评分
    save_evaluations(samples, path="data/pending_evaluations.jsonl")
    print("\n  → 等待 Mavis 在对话中给每个样本打分")
