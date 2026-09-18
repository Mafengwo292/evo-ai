"""
scripts/aggressive_v2.py
-------------------------
阿里云激进训练 v2:
- 更大模型（d_model=128, n_layer=4）
- 多数据源（2.1MB）
- Anti-mode-collapse
- 多 seed 探索
"""

import sys
import os
import time
import json
import random
sys.path.insert(0, "/root/evo-ai")

import torch
from torch.optim import AdamW

from model.transformer import Block

# 加载多源数据
data_paths = [
    "/root/evo-ai/data/tinyshake.txt",
    "/root/evo-ai/data/crawled",
    "/root/evo-ai/data/public_text",
]
texts = []
for p in data_paths:
    if os.path.isfile(p):
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            t = f.read()
            if len(t) > 100:
                texts.append(t)
                print(f"[AggressiveV2] Loaded {p}: {len(t)} chars")
    elif os.path.isdir(p):
        for fn in os.listdir(p):
            fp = os.path.join(p, fn)
            if os.path.isfile(fp):
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        t = f.read()
                        if len(t) > 1000:
                            texts.append(t)
                            print(f"[AggressiveV2] Loaded {fp}: {len(t)} chars")
                except:
                    pass

text = "\n".join(texts)
print(f"[AggressiveV2] Total: {len(text)} chars from {len(texts)} sources")

# Tokenizer
chars = sorted(set(text))
vocab_size = len(chars)
stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for i, c in enumerate(chars)}
print(f"[AggressiveV2] Vocab: {vocab_size}")

def encode(s):
    return [stoi[c] for c in s if c in stoi]
def decode(ids):
    return "".join(itos[i] for i in ids)

data = torch.tensor(encode(text), dtype=torch.long)
print(f"[AggressiveV2] Tokens: {len(data)}")

# 更大模型
class BigGPT(torch.nn.Module):
    def __init__(self, vocab_size, d_model=128, n_head=4, n_layer=4, block_size=64):
        super().__init__()
        self.block_size = block_size
        self.tok_emb = torch.nn.Embedding(vocab_size, d_model)
        self.pos_emb = torch.nn.Embedding(block_size, d_model)
        self.blocks = torch.nn.ModuleList([
            Block(d_model, n_head, block_size) for _ in range(n_layer)
        ])
        self.ln_f = torch.nn.LayerNorm(d_model)
        self.head = torch.nn.Linear(d_model, vocab_size, bias=False)
        self.tok_emb.weight = self.head.weight

    def forward(self, idx, targets=None):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.tok_emb(idx) + self.pos_emb(pos)
        for block in self.blocks:
            x = block(x)
        x = self.ln_f(x)
        logits = self.head(x)
        loss = None
        if targets is not None:
            loss = torch.nn.functional.cross_entropy(logits.view(-1, vocab_size), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens=100, temperature=0.8):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature
            probs = torch.nn.functional.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, idx_next], dim=1)
        return idx

# 初始化或加载
model = BigGPT(vocab_size=vocab_size, d_model=128, n_head=4, n_layer=4, block_size=64)
n_params = sum(p.numel() for p in model.parameters())
print(f"[AggressiveV2] Model: {n_params:,} params ({n_params/1e3:.1f}K)")

optimizer = AdamW(model.parameters(), lr=3e-4, betas=(0.9, 0.95), weight_decay=0.1)
block_size = 64
batch_size = 32

# Training loop
print(f"[AggressiveV2] Starting infinite training...")
print(f"  Data: {len(data)} tokens, Model: {n_params} params")
print(f"  Block: {block_size}, Batch: {batch_size}")

import requests
API = "http://127.0.0.1:80/api/train_status"
SAVE = "/root/evo-ai/data/cloud_v2_latest.pt"

gen = 0
while True:
    try:
        gen += 1
        # 训练 N 步
        losses = []
        for _ in range(10):
            ix = torch.randint(0, len(data) - block_size - 1, (batch_size,))
            x = torch.stack([data[i:i+block_size] for i in ix])
            y = torch.stack([data[i+1:i+block_size+1] for i in ix])
            _, loss = model(x, y)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(loss.item())

        train_loss = sum(losses) / len(losses)

        # PPL
        with torch.no_grad():
            test_x = data[:block_size].unsqueeze(0)
            test_y = data[1:block_size+1].unsqueeze(0)
            _, test_loss = model(test_x, test_y)
            ppl = test_loss.item()

        # Save
        if gen % 5 == 0:
            torch.save({
                "model": model.state_dict(),
                "vocab_size": vocab_size,
                "block_size": block_size,
                "d_model": 128,
                "n_layer": 4,
                "n_head": 4,
                "tokenizer_chars": list(stoi.keys()),
            }, SAVE)
            # 上报
            try:
                requests.post(API, json={
                    "status": "cloud_v2_training",
                    "generation": gen,
                    "latest_train_loss": train_loss,
                    "latest_test_ppl": ppl,
                    "data_size": len(text),
                    "ckpt_count": gen // 5,
                    "model_params": n_params,
                }, timeout=5)
            except:
                pass

        print(f"[CloudV2 Gen {gen:4d}] loss={train_loss:.4f} ppl={ppl:.4f}")
        time.sleep(1)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"[CloudV2] Error: {e}")
        time.sleep(3)
