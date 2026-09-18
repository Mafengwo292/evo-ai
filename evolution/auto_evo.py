"""
evolution/auto_evo.py
---------------------
自动进化循环（Auto-Evolution Loop）。

完全自我驱动，不需要任何外部信号：
1. 用当前模型生成样本
2. 用内部 self-reward 评估（不依赖外部）
3. 选 top K 加入 buffer
4. 训练下一代
5. 评估新一代
6. 循环

这就是真正的"自进化"：模型靠自己变强。
"""

from __future__ import annotations
import os
import sys
import time
import json
import shutil
import random
import torch
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from torch.optim import AdamW
from distributed.sandbox_train import TinyGPT, CharTokenizer, SHAKESPEARE_TEXT
from evolution.self_reward import SelfReward


class AutoEvoLoop:
    """
    自动进化循环。
    不需要任何外部信号，由模型自己驱动。
    """

    def __init__(
        self,
        init_ckpt: str = "checkpoints/sandbox-1.pt",
        save_dir: str = "checkpoints/auto_evo",
        steps_per_gen: int = 100,
        n_samples_per_prompt: int = 4,
        top_k_ratio: float = 0.4,
        prompts: Optional[List[str]] = None,
        block_size: int = 32,
        d_model: int = 64,
        device: str = "cpu",
    ):
        self.save_dir = save_dir
        self.steps_per_gen = steps_per_gen
        self.n_samples_per_prompt = n_samples_per_prompt
        self.top_k_ratio = top_k_ratio
        self.prompts = prompts or [
            "ROMEO:", "JULIET:", "HAMLET:", "MACBETH:",
            "KING RICHARD III:", "OPHELIA:", "PROSPERO:",
        ]
        self.block_size = block_size
        self.d_model = d_model
        self.device = device
        os.makedirs(save_dir, exist_ok=True)

        # 1) 加载初始模型
        self.load_model(init_ckpt)

        # 2) 内部 reward
        self.reward_fn = SelfReward(
            model=self.model,
            tokenizer=self.tokenizer,
            block_size=block_size,
        )

        # 3) 进化历史
        self.history: List[Dict] = []
        self.generation = 0
        self.global_step = 0

    def load_model(self, ckpt_path: str):
        """加载模型"""
        ckpt = torch.load(ckpt_path, weights_only=False)
        self.config = ckpt["config"]
        self.model = TinyGPT(
            vocab_size=self.config["vocab_size"],
            d_model=self.config.get("d_model", self.d_model),
            n_head=2,
            block_size=self.config["block_size"],
        )
        self.model.load_state_dict(ckpt["model"], strict=False)
        self.model.to(self.device)
        self.model.eval()

        # 重建 tokenizer
        chars = ckpt["tokenizer_chars"]
        self.tokenizer = CharTokenizer("")
        self.tokenizer.stoi = {c: i for i, c in enumerate(chars)}
        self.tokenizer.itos = {i: c for i, c in enumerate(chars)}
        self.tokenizer.vocab_size = len(chars)
        print(f"[AutoEvo] Loaded {ckpt_path}, {sum(p.numel() for p in self.model.parameters())} params")

    def _generate_samples(self, n: int = None) -> List[Dict]:
        """用当前模型生成一批样本"""
        n = n or self.n_samples_per_prompt
        samples = []
        self.model.eval()
        with torch.no_grad():
            for prompt in self.prompts:
                for _ in range(n):
                    ids = self.tokenizer.encode(prompt)
                    if not ids:
                        ids = [0]
                    x = torch.tensor([ids], dtype=torch.long, device=self.device)
                    out = self.model.generate(
                        x, max_new_tokens=random.randint(60, 150), temperature=0.85
                    )
                    text = self.tokenizer.decode(out[0].tolist())
                    samples.append({"prompt": prompt, "text": text})
        return samples

    def _select_top_k(self, samples: List[Dict], scores: List[float]) -> List[Dict]:
        """选 top K 样本"""
        n = max(1, int(len(samples) * self.top_k_ratio))
        indexed = sorted(zip(samples, scores), key=lambda x: x[1], reverse=True)
        return [s for s, _ in indexed[:n]]

    def _train_one_step_on_buffer(
        self,
        texts: List[str],
        epochs: int = 2,
    ) -> float:
        """用 buffer 训练一个 mini-loop"""
        if not texts:
            return 0.0

        # 把所有文本拼起来
        combined = "\n".join(texts)
        if len(combined) < self.block_size * 2:
            return 0.0

        data_ids = self.tokenizer.encode(combined)
        if len(data_ids) < self.block_size + 1:
            return 0.0
        data = torch.tensor(data_ids, dtype=torch.long, device=self.device)

        # 训练几个 epoch
        optimizer = AdamW(self.model.parameters(), lr=5e-4)
        self.model.train()
        total_loss = 0.0
        n_batches = 0

        for epoch in range(epochs):
            n_iter = max(10, len(data_ids) // (self.block_size * 4))
            for _ in range(n_iter):
                ix = torch.randint(0, len(data) - self.block_size - 1, (8,))
                x = torch.stack([data[i:i+self.block_size] for i in ix])
                y = torch.stack([data[i+1:i+self.block_size+1] for i in ix])
                _, loss = self.model(x, y)
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                total_loss += loss.item()
                n_batches += 1

        return total_loss / max(1, n_batches)

    def step(self) -> Dict:
        """
        一步自进化（完全自驱动）：
        1) 生成
        2) 内部 self-reward 评估
        3) 选 top K
        4) 训练下一代
        5) 记录
        """
        t0 = time.time()
        # 1) 生成
        samples = self._generate_samples()
        # 2) 内部评估
        scores = self.reward_fn.score_batch(samples)
        # 3) 选 top K
        top = self._select_top_k(samples, scores)
        top_texts = [s["text"] for s in top]

        # 4) 训练：用 top K + 原始数据
        # 把 top K 加到原始数据训练
        avg_score = sum(scores) / len(scores) if scores else 0
        top_avg = sum(self.reward_fn.score_batch(top)) / len(top) if top else 0
        train_loss = self._train_one_step_on_buffer(
            top_texts + [SHAKESPEARE_TEXT], epochs=1
        )

        # 5) 评估当前模型（生成新样本看 perplexity）
        self.model.eval()
        with torch.no_grad():
            test_text = SHAKESPEARE_TEXT[:200]
            test_ids = self.tokenizer.encode(test_text)[:self.block_size]
            if len(test_ids) >= 2:
                x = torch.tensor([test_ids[:-1]], dtype=torch.long)
                y = torch.tensor([test_ids[1:]], dtype=torch.long)
                _, test_loss = self.model(x, y)
                test_loss = test_loss.item()
            else:
                test_loss = -1.0

        self.generation += 1
        self.global_step += 1

        result = {
            "generation": self.generation,
            "n_samples": len(samples),
            "n_selected": len(top),
            "avg_score": round(avg_score, 4),
            "top_avg_score": round(top_avg, 4),
            "train_loss": round(train_loss, 4),
            "test_perplexity_loss": round(test_loss, 4),
            "buffer_size": len(self.reward_fn.buffer),
            "elapsed_s": round(time.time() - t0, 2),
            "reward_weights": self.reward_fn.weights,
        }
        self.history.append(result)
        return result

    def run(self, n_generations: int = 10, sleep_between: float = 0.5):
        """
        跑 N 代自动进化。
        """
        print("=" * 60)
        print(f"  Auto-Evolution Loop (Self-Driven)")
        print(f"  Generations: {n_generations}, samples/prompt: {self.n_samples_per_prompt}")
        print("=" * 60)

        for i in range(n_generations):
            result = self.step()
            print(f"\n[Gen {result['generation']:3d}] "
                  f"avg={result['avg_score']:.3f} "
                  f"top={result['top_avg_score']:.3f} "
                  f"train_loss={result['train_loss']:.3f} "
                  f"test_ppl={result['test_perplexity_loss']:.3f} "
                  f"buf={result['buffer_size']} "
                  f"({result['elapsed_s']}s)")

            # 定期保存
            if i % 3 == 0 or i == n_generations - 1:
                self.save(f"auto_gen{self.generation}.pt")

            # 自动调整 reward 权重（meta-evolution）
            if i > 0 and i % 3 == 0:
                self._adapt_reward_weights()

            time.sleep(sleep_between)

        # 总结
        self._summary()

    def save(self, filename: str = None):
        """保存当前模型 + 状态"""
        filename = filename or f"auto_gen{self.generation}.pt"
        path = os.path.join(self.save_dir, filename)
        torch.save({
            "model": self.model.state_dict(),
            "config": self.config,
            "tokenizer_chars": list(self.tokenizer.stoi.keys()),
            "generation": self.generation,
            "global_step": self.global_step,
            "history": self.history,
            "buffer_size": len(self.reward_fn.buffer),
        }, path)
        # 同步保存状态给公网
        self._publish_status(path)
        return path

    def _publish_status(self, model_path: str):
        """把状态发布给公网网站"""
        status = {
            "model_version": f"auto-gen{self.generation}",
            "generation": self.generation,
            "global_step": self.global_step,
            "params": sum(p.numel() for p in self.model.parameters()),
            "buffer_size": len(self.reward_fn.buffer),
            "latest_train_loss": self.history[-1]["train_loss"] if self.history else None,
            "latest_test_ppl": self.history[-1]["test_perplexity_loss"] if self.history else None,
            "latest_avg_score": self.history[-1]["avg_score"] if self.history else None,
            "model_path": model_path,
            "updated_at": time.time(),
            "reward_weights": self.reward_fn.weights,
            "auto_driven": True,
            "history": self.history[-10:],   # 最近 10 代
        }
        status_path = "data/auto_evo_status.json"
        os.makedirs(os.path.dirname(status_path), exist_ok=True)
        with open(status_path, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
        # 复制最新权重到标准位置（网站拉取用）
        public_path = "data/latest_model.pt"
        if os.path.exists(model_path):
            shutil.copy(model_path, public_path)
        # 状态文件也复制一个 public 版本
        public_status = "data/latest_status.json"
        with open(public_status, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
        print(f"  [Published] {status_path} + {public_status}")

    def _adapt_reward_weights(self):
        """
        Meta-evolution：根据近期表现调整 reward 权重。
        如果多样性分一直在掉 → 增加 diversity 权重
        如果格式分低 → 增加 format 权重
        """
        if len(self.history) < 3:
            return
        recent = self.history[-3:]
        avg_train_loss = sum(h["train_loss"] for h in recent) / len(recent)
        avg_score = sum(h["avg_score"] for h in recent) / len(recent)

        # 简单策略：如果 loss 没降，增加 perplexity 权重
        if avg_train_loss > 2.0:
            self.reward_fn.weights["perplexity"] = min(0.4, self.reward_fn.weights["perplexity"] + 0.05)
            self.reward_fn.weights["diversity"] = max(0.1, self.reward_fn.weights["diversity"] - 0.05)
            print(f"  [Meta] Adjusted weights: {self.reward_fn.weights}")
        elif avg_score > 0.7:
            # 表现好，可以更多关注新颖度
            self.reward_fn.weights["novelty"] = min(0.3, self.reward_fn.weights["novelty"] + 0.05)
            self.reward_fn.weights["format"] = max(0.1, self.reward_fn.weights["format"] - 0.05)
            print(f"  [Meta] Adjusted weights: {self.reward_fn.weights}")

    def _summary(self):
        print(f"\n{'='*60}")
        print(f"  Auto-Evolution Complete")
        print(f"{'='*60}")
        if self.history:
            first = self.history[0]
            last = self.history[-1]
            print(f"  Gen 0  → Gen {last['generation']}")
            print(f"  Avg score: {first['avg_score']:.3f} → {last['avg_score']:.3f}")
            print(f"  Test ppl: {first['test_perplexity_loss']:.3f} → {last['test_perplexity_loss']:.3f}")
            print(f"  Buffer: {last['buffer_size']} samples")
        print()
        print(f"  Trajectory:")
        for h in self.history:
            bar_len = int(h["avg_score"] * 30)
            bar = "█" * bar_len
            print(f"    Gen {h['generation']:3d}: avg={h['avg_score']:.3f} {bar}")


def run_forever(init_ckpt: str = "checkpoints/sandbox-1.pt", gen_interval_s: float = 30.0):
    """
    永真循环：永远自动进化。
    每代之间 sleep。
    """
    print("[AutoEvo] Starting FOREVER auto-evolution loop")
    print(f"[AutoEvo] Press Ctrl+C to stop")
    loop = AutoEvoLoop(init_ckpt=init_ckpt)
    gen = 0
    while True:
        try:
            result = loop.step()
            gen += 1
            print(f"[AutoEvo Gen {gen:4d}] avg={result['avg_score']:.3f} "
                  f"loss={result['train_loss']:.3f} ppl={result['test_perplexity_loss']:.3f}")
            if gen % 5 == 0:
                loop.save()
                loop._adapt_reward_weights()
            time.sleep(gen_interval_s)
        except KeyboardInterrupt:
            print("\n[AutoEvo] Stopped by user")
            loop.save("auto_final.pt")
            break
        except Exception as e:
            print(f"[AutoEvo] Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(10)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", default="checkpoints/sandbox-1.pt")
    parser.add_argument("--gens", type=int, default=10)
    parser.add_argument("--sleep", type=float, default=0.3)
    parser.add_argument("--forever", action="store_true")
    parser.add_argument("--interval", type=float, default=30.0)
    args = parser.parse_args()

    if args.forever:
        run_forever(args.init, args.interval)
    else:
        loop = AutoEvoLoop(init_ckpt=args.init)
        loop.run(n_generations=args.gens, sleep_between=args.sleep)
