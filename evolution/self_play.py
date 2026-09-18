"""
evolution/self_play.py
----------------------
自生成数据循环（Self-Play / Self-Training）。

核心循环：
1. 用当前模型生成新数据
2. 用 reward function 评估
3. 选 top K 加入训练集
4. 重新训练下一代模型
5. 下一代写出更好的数据
6. 循环

这是"自进化"的核心机制 —— 模型靠自己变强。
"""

from __future__ import annotations
import os
import sys
import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evolution.data_generator import DataGenerator, GeneratedSample, mock_generate
from evolution.reward import heuristic_reward, reward_batch


@dataclass
class TrainingBuffer:
    """训练数据缓冲区"""
    samples: List[GeneratedSample] = field(default_factory=list)
    max_size: int = 5000

    def add(self, sample: GeneratedSample):
        self.samples.append(sample)
        # 按 reward 排序，保留高分样本
        if len(self.samples) > self.max_size:
            self.samples.sort(key=lambda s: s.reward, reverse=True)
            self.samples = self.samples[:self.max_size]

    def get_training_texts(self, top_k: int = None) -> List[str]:
        """按 reward 排序取出训练文本"""
        sorted_samples = sorted(self.samples, key=lambda s: s.reward, reverse=True)
        if top_k:
            sorted_samples = sorted_samples[:top_k]
        return [s.text for s in sorted_samples]

    def stats(self) -> Dict:
        if not self.samples:
            return {"n": 0}
        rewards = [s.reward for s in self.samples]
        return {
            "n": len(self.samples),
            "avg_reward": sum(rewards) / len(rewards),
            "max_reward": max(rewards),
            "min_reward": min(rewards),
        }


class SelfPlayLoop:
    """
    自生成数据驱动的进化循环。
    """

    def __init__(
        self,
        data_generator: DataGenerator,
        buffer: TrainingBuffer = None,
        prompts: List[str] = None,
        n_per_prompt: int = 4,
        top_k_ratio: float = 0.5,
    ):
        self.gen = data_generator
        self.buffer = buffer or TrainingBuffer()
        self.prompts = prompts or [
            "\n", "ROMEO:", "JULIET:", "HAMLET:",
            "KING RICHARD:", "The ", "In ", "My ",
        ]
        self.n_per_prompt = n_per_prompt
        self.top_k_ratio = top_k_ratio
        self.generation = 0
        self.history: List[Dict] = []

    def _evaluate(self, samples: List[GeneratedSample]) -> List[GeneratedSample]:
        """评估所有样本的 reward"""
        texts = [s.text for s in samples]
        rewards = reward_batch(texts)
        for s, r in zip(samples, rewards):
            s.reward = r
        return samples

    def _select_top_k(self, samples: List[GeneratedSample]) -> List[GeneratedSample]:
        """选 top K"""
        samples.sort(key=lambda s: s.reward, reverse=True)
        k = max(1, int(len(samples) * self.top_k_ratio))
        return samples[:k]

    def _simulate_training_step(self, n_samples: int) -> float:
        """
        模拟训练（真实环境会调 training.trainer.train）。
        返回"训练后的质量提升"。
        """
        # 训练数据越多、质量越高，下一代模型质量越好
        stats = self.buffer.stats()
        if stats["n"] == 0:
            return self.gen.model_quality

        avg_reward = stats["avg_reward"]
        # 简单线性映射：avg_reward 越高，下一代 quality 提升越大
        # 但有上限，且不是单步就完美
        improvement = avg_reward * 0.1
        new_quality = min(0.95, self.gen.model_quality + improvement)
        return new_quality

    def step(self) -> Dict:
        """
        一步自进化：
        1) 生成
        2) 评估
        3) 选 top K
        4) 加进 buffer
        5) 模拟训练
        6) 更新模型质量
        """
        # 1) 生成
        samples = self.gen.generate(self.prompts, self.n_per_prompt)
        # 2) 评估
        samples = self._evaluate(samples)
        # 3) 选 top K
        top_samples = self._select_top_k(samples)
        # 4) 加进 buffer
        for s in top_samples:
            self.buffer.add(s)
        # 5) 模拟训练
        old_quality = self.gen.model_quality
        new_quality = self._simulate_training_step(len(top_samples))
        self.gen.model_quality = new_quality
        # 6) 记录
        self.generation += 1
        avg_reward = sum(s.reward for s in samples) / len(samples) if samples else 0
        top_avg = sum(s.reward for s in top_samples) / len(top_samples) if top_samples else 0
        result = {
            "generation": self.generation,
            "n_generated": len(samples),
            "n_selected": len(top_samples),
            "avg_reward": round(avg_reward, 4),
            "top_avg_reward": round(top_avg, 4),
            "old_quality": round(old_quality, 4),
            "new_quality": round(new_quality, 4),
            "buffer_stats": self.buffer.stats(),
        }
        self.history.append(result)
        return result

    def run(self, n_steps: int = 10) -> List[Dict]:
        """跑 N 步自进化"""
        print("=" * 60)
        print(f"  Self-Play Self-Evolution Loop")
        print(f"  Steps: {n_steps}, Prompts: {len(self.prompts)}, n/prompt: {self.n_per_prompt}")
        print("=" * 60)

        for i in range(n_steps):
            result = self.step()
            print(f"\n[Gen {result['generation']:3d}] "
                  f"avg_r={result['avg_reward']:.3f} "
                  f"top_r={result['top_avg_reward']:.3f} "
                  f"quality: {result['old_quality']:.3f} → {result['new_quality']:.3f} "
                  f"buffer={result['buffer_stats']['n']}")
            time.sleep(0.05)

        # 总结
        print(f"\n{'='*60}")
        print(f"  Self-Play Complete")
        print(f"{'='*60}")
        print(f"Final model quality: {self.gen.model_quality:.3f}")
        print(f"Buffer size: {self.buffer.stats()['n']}")
        print(f"Reward trajectory:")
        for h in self.history:
            bar = "█" * int(h["new_quality"] * 30)
            print(f"  Gen {h['generation']:3d}: {h['new_quality']:.3f} {bar}")

        return self.history
