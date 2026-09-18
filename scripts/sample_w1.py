"""
scripts/sample_w1.py
--------------------
加载训练好的模型，生成文本。

用法：
  python scripts/sample_w1.py [--ckpt checkpoints/gpt_w1.pt] [--max_tokens 500]
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from model.gpt import GPT, GPTConfig
from data.dataset import CharTokenizer, download_tinyshakespeare


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", type=str, default="checkpoints/gpt_w1.pt")
    parser.add_argument("--max_tokens", type=int, default=500)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top_k", type=int, default=200)
    parser.add_argument("--start", type=str, default="\n")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # 1) 加载 checkpoint
    print(f"[Load] {args.ckpt}")
    ckpt = torch.load(args.ckpt, map_location=device, weights_only=False)
    cfg = GPTConfig(**ckpt["config"])
    model = GPT(cfg).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()

    # 2) 重新构建 tokenizer（用同样的数据）
    path = download_tinyshakespeare()
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    tok = CharTokenizer(text)

    # 3) 生成
    start_ids = tok.encode(args.start)
    if not start_ids:
        start_ids = [0]
    x = torch.tensor(start_ids, dtype=torch.long, device=device)[None, ...]

    print(f"\n[Gen] Prompt: {args.start!r}")
    print(f"[Gen] max_tokens={args.max_tokens}, temperature={args.temperature}, top_k={args.top_k}")
    print("=" * 60)

    out = model.generate(x, max_new_tokens=args.max_tokens,
                         temperature=args.temperature, top_k=args.top_k)
    print(tok.decode(out[0].tolist()))
    print("=" * 60)


if __name__ == "__main__":
    main()
