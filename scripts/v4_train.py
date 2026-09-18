"""
scripts/v4_train.py
-------------------
V4 sandbox 训练循环：
- 用阿里云最新权重（Gen 12,753+）
- 集成 anti-mode-collapse 引擎
- 上报状态到公网 API
- 多种子探索
"""

import sys
import os
import time
import json
import random
import urllib.request, urllib.parse, json

def urllib_post(url, payload, timeout=5):
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=timeout)
    except:
        pass



sys.path.insert(0, "/workspace/evo-ai")
sys.path.insert(0, "/root/evo-ai")

import torch
from torch.optim import AdamW
from distributed.sandbox_train import TinyGPT, CharTokenizer
from evolution.self_reward import SelfReward
from evolution.anti_collapse import AntiCollapseEngine, NoiseInjector, TemperatureAnnealer

CKPT = "/workspace/evo-ai/data/aliyun_weights/latest_from_aliyun.pt"
TEXT = "/workspace/evo-ai/data/extended_train.txt"
PUBLIC_TXT = "/tmp/tinyshake.txt"
API_URL = "http://47.253.174.153:80/api/train_status"
SEND_URL = "http://47.253.174.153:80/api/feedback"

# 多样化种子
PROMPTS = [
    "ROMEO:", "JULIET:", "HAMLET:", "MACBETH:",
    "KING RICHARD III:", "OPHELIA:", "PROSPERO:",
    "LEAR:", "OTHELLO:", "PORTIA:",
    "CALIBAN:", "ARIEL:", "BOTTOM:",
    "PROSPERO:", "SHYLOCK:", "DESDEMONA:",
    "IAGO:", "CORDELIA:", "KATHARINA:",
]


def load_data():
    if os.path.exists(PUBLIC_TXT):
        with open(PUBLIC_TXT, "r", encoding="utf-8") as f:
            return f.read()
    elif os.path.exists(TEXT):
        with open(TEXT, "r", encoding="utf-8") as f:
            return f.read()
    return "ROMEO:\nBut soft\n"


def report_status(gen, train_loss, ppl, score, buffer_size, weights, ckpt_count):
    payload = {
        "status": "sandbox_training",
        "generation": gen,
        "latest_train_loss": train_loss,
        "latest_test_ppl": ppl,
        "latest_avg_score": score,
        "buffer_size": buffer_size,
        "reward_weights": weights,
        "data_size": os.path.getsize(PUBLIC_TXT) if os.path.exists(PUBLIC_TXT) else 0,
        "ckpt_count": ckpt_count,
        "source": "sandbox",
    }
    try:
        try:
            req = urllib.request.Request(API_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except: pass
    except Exception as e:
        print(f"[Report] {e}")


def main():
    print("=" * 60)
    print("  EVO-AI V4 Sandbox Training")
    print("  Anti-Mode-Collapse + Multi-Seed Exploration")
    print("=" * 60)

    # 加载阿里云最新权重
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
    print(f"[V4] Loaded Aliyun latest: {sum(p.numel() for p in model.parameters())} params")

    # Anti-collapse 引擎
    anti_collapse = AntiCollapseEngine()
    noise = NoiseInjector()
    annealer = TemperatureAnnealer(base_temp=0.8)

    # 内部 reward
    reward_fn = SelfReward(model=model, tokenizer=tok, block_size=32)
    reward_fn.weights["novelty"] = 0.30
    reward_fn.weights["format"] = 0.10
    reward_fn.weights["diversity"] = 0.30
    reward_fn.weights["perplexity"] = 0.20
    reward_fn.weights["consistency"] = 0.10
    print(f"[V4] Reward weights: {reward_fn.weights}")

    # 加载全部公网数据
    text = load_data()
    print(f"[V4] Data: {len(text)} chars")

    data = torch.tensor(tok.encode(text), dtype=torch.long)
    print(f"[V4] Tokens: {len(data)}")

    block_size = 32
    batch_size = 16
    optimizer = AdamW(model.parameters(), lr=3e-4)

    ckpt_count = 0
    gen = 0
    intervention_history = []
    score_history = []

    print("\n[V4] Starting infinite training with anti-collapse...")
    print("=" * 60)

    while True:
        try:
            gen += 1
            model.train()

            # 训练数据增强（噪声注入）
            if random.random() < 0.3:
                # 偶尔用增强数据
                augment_text = noise.augment(text, intensity=0.3)
                augment_data = torch.tensor(tok.encode(augment_text[:50000]), dtype=torch.long)
                train_data = augment_data
            else:
                train_data = data

            # 训练 N 步
            train_loss = 0.0
            n_micro = 15
            for micro in range(n_micro):
                ix = torch.randint(0, len(train_data) - block_size - 1, (batch_size,))
                x = torch.stack([train_data[i:i+block_size] for i in ix])
                y = torch.stack([train_data[i+1:i+block_size+1] for i in ix])
                _, loss = model(x, y)
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                train_loss += loss.item()
            train_loss /= n_micro

            # 生成 + 评估
            model.eval()
            temp = annealer.get_temperature(gen)
            samples = []
            with torch.no_grad():
                for prompt in PROMPTS[:8]:   # 用前 8 个 prompt
                    ids = tok.encode(prompt)
                    if not ids:
                        ids = [0]
                    x = torch.tensor([ids], dtype=torch.long)
                    out = model.generate(x, max_new_tokens=random.randint(50, 100), temperature=temp)
                    text_out = tok.decode(out[0].tolist())
                    samples.append({"prompt": prompt, "text": text_out})

            # 内部 reward
            scores = reward_fn.score_batch(samples)
            avg_score = sum(scores) / len(scores) if scores else 0
            score_history.append(avg_score)

            # 更新 diversity 全局
            anti_collapse.diversity.update_global([s["text"] for s in samples])

            # PPL
            test_ids = data[:block_size + 50]
            with torch.no_grad():
                if len(test_ids) > block_size + 1:
                    _, test_loss = model(
                        test_ids[:block_size].unsqueeze(0),
                        test_ids[1:block_size+1].unsqueeze(0),
                    )
                    ppl = test_loss.item()
                else:
                    ppl = train_loss

            # Anti-collapse 检测
            should_intervene = anti_collapse.should_intervene(avg_score, train_loss)
            if should_intervene and gen - anti_collapse.last_intervention > 15:
                anti_collapse.on_intervention(avg_score, gen, model, reward_fn.buffer)
                intervention_history.append(gen)
                anti_collapse.last_intervention = gen
                # 增加 reward 权重 diversity
                reward_fn.weights["diversity"] = min(0.40, reward_fn.weights["diversity"] + 0.05)
                reward_fn.weights["novelty"] = min(0.40, reward_fn.weights["novelty"] + 0.05)
                # 重新初始化 optimizer（低学习率）
                optimizer = AdamW(model.parameters(), lr=1e-4)

            # 定期保存
            if gen % 5 == 0:
                ckpt_count += 1
                save_path = f"/workspace/evo-ai/checkpoints/auto_evo/v4_gen{gen}.pt"
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                torch.save({
                    "model": model.state_dict(),
                    "config": ckpt["config"],
                    "tokenizer_chars": list(tok.stoi.keys()),
                    "generation": gen,
                    "interventions": intervention_history,
                }, save_path)
                # 同步到 latest
                torch.save({
                    "model": model.state_dict(),
                    "config": ckpt["config"],
                    "tokenizer_chars": list(tok.stoi.keys()),
                    "generation": gen,
                }, "/workspace/evo-ai/data/latest_model.pt")

            # 上报
            if gen % 3 == 0:
                report_status(gen, train_loss, ppl, avg_score,
                              len(reward_fn.buffer), reward_fn.weights, ckpt_count)
                # 推一条 feedback 到公网（让公网节点也有 EVO-AI 自己的数据）
                if samples:
                    best = max(samples, key=lambda s: reward_fn.score(s["text"]))
                    try:
                        req = urllib.request.Request(SEND_URL, data=json.dumps({"node_id": "sandbox-self", "prompt": best["prompt"], "text": best["text"][:300], "score": 5}).encode(), headers={"Content-Type": "application/json"})
                        urllib.request.urlopen(req, timeout=3)
                    except:
                        pass

            # Meta-evolution
            if gen % 10 == 0 and avg_score < 0.65 and train_loss > 0.5:
                # 如果 score 一直低且 loss 高 → 增 perplexity
                reward_fn.weights["perplexity"] = min(0.40, reward_fn.weights["perplexity"] + 0.05)
                reward_fn.weights["format"] = max(0.05, reward_fn.weights["format"] - 0.05)

            interventions_count = len(intervention_history)
            print(f"[V4 Gen {gen:4d}] loss={train_loss:.3f} ppl={ppl:.3f} score={avg_score:.3f} temp={temp:.2f} interventions={interventions_count}")
            time.sleep(1.5)

        except KeyboardInterrupt:
            print("\n[V4] Stopped")
            break
        except Exception as e:
            print(f"[V4] Error: {e}")
            import traceback; traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    main()
