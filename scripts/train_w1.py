"""
scripts/train_w1.py
-------------------
W1 训练入口：从零训练一个 nanoGPT。

用法：
  python scripts/train_w1.py [--steps 2000] [--batch 32] [--d_model 192] [--n_layer 6]
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.gpt import GPTConfig
from training.trainer import train


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--block_size", type=int, default=256)
    parser.add_argument("--d_model", type=int, default=192)
    parser.add_argument("--n_layer", type=int, default=6)
    parser.add_argument("--n_head", type=int, default=6)
    parser.add_argument("--save", type=str, default="checkpoints/gpt_w1.pt")
    args = parser.parse_args()

    cfg = GPTConfig(
        block_size=args.block_size,
        vocab_size=65,    # Tiny Shakespeare 字符数
        n_layer=args.n_layer,
        n_head=args.n_head,
        d_model=args.d_model,
        dropout=0.0,
    )

    print("=" * 60)
    print("  Evo-AI · W1: 从零训练 nanoGPT")
    print("=" * 60)
    print(f"  block_size: {cfg.block_size}")
    print(f"  d_model:    {cfg.d_model}")
    print(f"  n_layer:    {cfg.n_layer}")
    print(f"  n_head:     {cfg.n_head}")
    print(f"  steps:      {args.steps}")
    print(f"  batch:      {args.batch}")
    print(f"  lr:         {args.lr}")
    print("=" * 60)

    model, tok = train(
        config=cfg,
        max_steps=args.steps,
        batch_size=args.batch,
        max_lr=args.lr,
        save_path=args.save,
    )
    print("\n训练完成！用 python scripts/sample_w1.py 看效果。")


if __name__ == "__main__":
    main()
