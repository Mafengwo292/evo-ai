"""
scripts/aggressive_train.py
---------------------------
激进训练脚本：使用全部 1.1MB 公网 Shakespeare 数据
每代训练后自动上报状态到公网 API
让公网用户实时看到模型进化
"""

import sys
import os
import time
import json
import requests
sys.path.insert(0, "/root/evo-ai")

import torch
from torch.optim import AdamW

from model.gpt import GPT, GPTConfig
from distributed.sandbox_train import TinyGPT, CharTokenizer
from evolution.self_reward import SelfReward

CKPT = "/root/evo-ai/data/latest_model.pt"
TEXT = "/root/evo-ai/data/tinyshake.txt"
API_URL = "http://47.253.174.153:80/api/train_status"


def load_data():
    """加载全部公网数据"""
    if os.path.exists(TEXT):
        with open(TEXT, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = "ROMEO:\nBut soft what light\n"
    print(f"[AggressiveTrain] Data: {len(text)} chars")
    return text


def report_status(generation, train_loss, ppl, score, buffer_size, weights):
    """上报状态到公网 API"""
    payload = {
        "status": "training",
        "generation": generation,
        "latest_train_loss": train_loss,
        "latest_test_ppl": ppl,
        "latest_avg_score": score,
        "buffer_size": buffer_size,
        "reward_weights": weights,
        "data_size": os.path.getsize(TEXT) if os.path.exists(TEXT) else 0,
        "ckpt_count": len([f for f in os.listdir("/root/evo-ai/checkpoints/auto_evo") if f.endswith(".pt")]) if os.path.exists("/root/evo-ai/checkpoints/auto_evo") else 0,
    }
    try:
        r = requests.post(API_URL, json=payload, timeout=5)
        if r.status_code == 200:
            print(f"[Report] Gen {generation} status reported")
    except Exception as e:
        print(f"[Report] Failed: {e}")


def main():
    # 加载模型
    ckpt = torch.load(CKPT, weights_only=False)
    chars = ckpt["tokenizer_chars"]
    tok = CharTokenizer("")
    tok.stoi = {c: i for i, c in enumerate(chars)}
    tok.itos = {i: c for i, c in enumerate(chars)}
    tok.vocab_size = len(chars)

    model = TinyGPT(
        vocab_size=ckpt["config"]["vocab_size"],
        d_model=ckpt["config"]["d_model"],
        n_head=2,
        block_size=ckpt["config"]["block_size"],
    )
    model.load_state_dict(ckpt["model"], strict=False)

    # 加载全部数据
    text = load_data()
    data = torch.tensor(tok.encode(text), dtype=torch.long)
    print(f"[AggressiveTrain] Tokens: {len(data)}")

    # 内部 reward
    reward_fn = SelfReward(model=model, tokenizer=tok, block_size=32)
    reward_fn.weights["novelty"] = 0.25
    reward_fn.weights["format"] = 0.15
    reward_fn.weights["diversity"] = 0.25
    reward_fn.weights["perplexity"] = 0.25
    reward_fn.weights["consistency"] = 0.10

    prompts = ["ROMEO:", "JULIET:", "HAMLET:", "MACBETH:",
               "KING RICHARD III:", "OPHELIA:", "PROSPERO:",
               "LEAR:", "OTHELLO:", "PORTIA:"]

    block_size = 32
    batch_size = 16
    optimizer = AdamW(model.parameters(), lr=5e-4)

    print(f"[AggressiveTrain] Starting infinite aggressive training...")
    print(f"  Data: {len(text)} chars ({len(data)} tokens)")
    print(f"  Block size: {block_size}, Batch: {batch_size}")
    print(f"  Reporting to {API_URL}")
    print()

    gen = 0
    last_report = 0

    while True:
        try:
            gen += 1
            model.train()

            # 1) 用大 batch 训练
            for micro in range(20):  # 每代 20 个 micro-step
                ix = torch.randint(0, len(data) - block_size - 1, (batch_size,))
                x = torch.stack([data[i:i+block_size] for i in ix])
                y = torch.stack([data[i+1:i+block_size+1] for i in ix])
                _, loss = model(x, y)
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()

            train_loss = loss.item()

            # 2) 生成样本 + 评估
            model.eval()
            samples = []
            with torch.no_grad():
                for prompt in prompts:
                    ids = tok.encode(prompt)
                    if not ids:
                        ids = [0]
                    x = torch.tensor([ids], dtype=torch.long)
                    out = model.generate(x, max_new_tokens=random.randint(60, 120), temperature=0.85)
                    text = tok.decode(out[0].tolist())
                    samples.append({"prompt": prompt, "text": text})

            # 3) 内部 reward
            scores = reward_fn.score_batch(samples)
            avg_score = sum(scores) / len(scores)

            # 4) Test perplexity
            test_ids = data[:block_size + 50]
            if len(test_ids) > block_size + 1:
                with torch.no_grad():
                    _, test_loss = model(
                        test_ids[:block_size].unsqueeze(0),
                        test_ids[1:block_size+1].unsqueeze(0),
                    )
                ppl = test_loss.item()
            else:
                ppl = train_loss

            # 5) 保存 checkpoint
            if gen % 5 == 0:
                save_path = f"/root/evo-ai/checkpoints/auto_evo/cloud_gen{gen}.pt"
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                torch.save({
                    "model": model.state_dict(),
                    "config": ckpt["config"],
                    "tokenizer_chars": list(tok.stoi.keys()),
                    "generation": gen,
                    "data_size": len(text),
                }, save_path)
                # 也更新 latest
                latest = "/root/evo-ai/data/latest_model.pt"
                torch.save({
                    "model": model.state_dict(),
                    "config": ckpt["config"],
                    "tokenizer_chars": list(tok.stoi.keys()),
                    "generation": gen,
                }, latest)

            # 6) 上报状态
            if gen - last_report >= 3 or gen == 1:
                report_status(gen, train_loss, ppl, avg_score,
                              len(reward_fn.buffer), reward_fn.weights)
                last_report = gen

            # 7) Meta-evolution: 根据表现调整 reward 权重
            if gen > 0 and gen % 8 == 0:
                # 如果 loss 在下降但 score 卡住 → 增 novelty
                if train_loss < 0.30 and avg_score < 0.65:
                    reward_fn.weights["novelty"] = min(0.40, reward_fn.weights["novelty"] + 0.05)
                    reward_fn.weights["format"] = max(0.05, reward_fn.weights["format"] - 0.05)
                    print(f"  [Meta] weights: {reward_fn.weights}")

            print(f"[Gen {gen:4d}] loss={train_loss:.4f} ppl={ppl:.4f} score={avg_score:.3f} buf={len(reward_fn.buffer)}")
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n[AggressiveTrain] Stopped by user")
            break
        except Exception as e:
            print(f"[AggressiveTrain] Error: {e}")
            import traceback; traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    import random
    main()
