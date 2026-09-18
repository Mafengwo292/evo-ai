"""
evolution/anti_collapse.py
---------------------------
Anti-Mode-Collapse Reward Functions.

当模型在自驱动训练中陷入"模式坍缩"（只生成类似文本，loss 下降但 score 停滞），
用以下机制打破：

1. KL Divergence to Anchor：和"锚点"模型的输出分布保持距离
2. Temperature Diversity：周期性提高 temperature，强制探索
3. Noise Injection：在训练数据中加入随机扰动
4. Population Diversity：跟踪 n-gram 分布，奖励新模式
5. Mode Reset：当 score 长期不涨时，重启 buffer
6. Cross-Model Crossover：和其他模型变体的输出混合
"""

from __future__ import annotations
import torch
import torch.nn.functional as F
import random
import math
from collections import Counter
from typing import List, Dict, Optional, Tuple
import hashlib


class AntiCollapseMonitor:
    """
    监控模式坍塌信号。
    """

    def __init__(self, window: int = 20, collapse_threshold: float = 0.005):
        self.window = window
        self.collapse_threshold = collapse_threshold
        self.score_history: List[float] = []
        self.loss_history: List[float] = []
        self.collapse_detected_count = 0
        self.last_intervention = -100

    def update(self, score: float, loss: float) -> bool:
        """更新状态，返回是否需要干预"""
        self.score_history.append(score)
        self.loss_history.append(loss)
        if len(self.score_history) > self.window:
            self.score_history.pop(0)
            self.loss_history.pop(0)

        if len(self.score_history) < self.window:
            return False

        # 检测 1: score 在最近 N 代几乎没有变化
        recent_max = max(self.score_history[-self.window:])
        recent_min = min(self.score_history[-self.window:])
        score_variance = recent_max - recent_min

        # 检测 2: loss 卡在很小范围
        loss_variance = max(self.loss_history[-self.window:]) - min(self.loss_history[-self.window:])

        is_collapsing = (
            score_variance < self.collapse_threshold and
            loss_variance < 0.02
        )

        if is_collapsing:
            self.collapse_detected_count += 1
        else:
            self.collapse_detected_count = max(0, self.collapse_detected_count - 1)

        # 持续 3 次检测到坍缩 → 触发干预
        return self.collapse_detected_count >= 3


class DiversityReward:
    """
    多样性 reward：跟踪 n-gram 分布，奖励新模式。
    """

    def __init__(self, n: int = 4):
        self.n = n
        self.global_ngram_counts: Counter = Counter()
        self.local_window: List[str] = []   # 最近的生成
        self.window_size = 50

    def update_global(self, texts: List[str]):
        """更新全局 n-gram 统计"""
        for text in texts:
            words = text.lower().split()
            for i in range(len(words) - self.n + 1):
                ngram = " ".join(words[i:i+self.n])
                self.global_ngram_counts[ngram] += 1

        # 限制大小
        if len(self.global_ngram_counts) > 10000:
            # 保留高频
            self.global_ngram_counts = Counter(dict(
                self.global_ngram_counts.most_common(5000)
            ))

    def score(self, text: str) -> float:
        """
        评分：n-gram 在 global 中越不常见 → 分数越高
        """
        words = text.lower().split()
        if len(words) < self.n:
            return 0.5

        total_weight = 0.0
        novelty_score = 0.0
        for i in range(len(words) - self.n + 1):
            ngram = " ".join(words[i:i+self.n])
            count = self.global_ngram_counts.get(ngram, 0)
            # 出现越少 → 越新
            if count == 0:
                novelty_score += 1.0
            elif count < 3:
                novelty_score += 0.5
            else:
                novelty_score += 0.1
            total_weight += 1.0

        return novelty_score / max(total_weight, 1.0)


class NoiseInjector:
    """
    训练数据噪声注入。
    """

    @staticmethod
    def inject_char_noise(text: str, prob: float = 0.02) -> str:
        """字符级随机替换"""
        chars = list(text)
        for i in range(len(chars)):
            if random.random() < prob:
                chars[i] = random.choice('abcdefghijklmnopqrstuvwxyz \n')
        return "".join(chars)

    @staticmethod
    def inject_swap_noise(text: str, prob: float = 0.01) -> str:
        """字符交换"""
        chars = list(text)
        for i in range(len(chars) - 1):
            if random.random() < prob:
                chars[i], chars[i+1] = chars[i+1], chars[i]
        return "".join(chars)

    @staticmethod
    def inject_shuffle_lines(text: str, prob: float = 0.05) -> str:
        """行级乱序"""
        lines = text.split("\n")
        result = []
        for line in lines:
            if random.random() < prob and len(lines) > 1:
                # 随机抽另一行换位置
                other = random.choice(lines)
                result.append(other)
            else:
                result.append(line)
        return "\n".join(result)

    @classmethod
    def augment(cls, text: str, intensity: float = 0.5) -> str:
        """组合噪声"""
        if random.random() < intensity * 0.3:
            text = cls.inject_char_noise(text, prob=0.01 * intensity)
        if random.random() < intensity * 0.2:
            text = cls.inject_swap_noise(text, prob=0.005 * intensity)
        if random.random() < intensity * 0.1:
            text = cls.inject_shuffle_lines(text, prob=0.02 * intensity)
        return text


class TemperatureAnnealer:
    """
    周期性调整生成 temperature，避免模型收敛到单一模式。
    """

    def __init__(self, base_temp: float = 0.8):
        self.base = base_temp
        self.cycle = 0

    def get_temperature(self, gen: int) -> float:
        """周期性变化：每 10 代一个周期"""
        phase = gen % 10
        if phase < 3:
            # 高温探索
            return self.base * 1.5
        elif phase < 7:
            # 正常
            return self.base
        else:
            # 低温聚焦
            return self.base * 0.6


class BufferResetter:
    """
    当 score 长期不涨，重置 buffer 引入新数据。
    """

    def __init__(self, reset_threshold: int = 50):
        self.reset_threshold = reset_threshold
        self.samples_since_reset = 0
        self.last_reset_gen = -100
        self.last_score_at_reset = 0.0

    def should_reset(self, score: float, gen: int) -> bool:
        if gen - self.last_reset_gen < 20:   # 至少间隔 20 代
            return False
        if score > self.last_score_at_reset + 0.05:   # 有改善就不重置
            return False
        return self.samples_since_reset >= self.reset_threshold

    def reset(self, score: float, gen: int):
        self.samples_since_reset = 0
        self.last_reset_gen = gen
        self.last_score_at_reset = score


class AntiCollapseEngine:
    """
    完整的 anti-mode-collapse 引擎。
    把所有机制组合起来。
    """

    def __init__(self):
        self.monitor = AntiCollapseMonitor()
        self.diversity = DiversityReward()
        self.noise = NoiseInjector()
        self.annealer = TemperatureAnnealer()
        self.resetter = BufferResetter()
        self.intervention_count = 0

    def should_intervene(self, score: float, loss: float) -> bool:
        return self.monitor.update(score, loss)

    def get_training_params(self, gen: int, base_temp: float = 0.8) -> Dict:
        """根据当前状态返回训练参数"""
        return {
            "temperature": self.annealer.get_temperature(gen),
            "noise_intensity": 0.3 if self.intervention_count > 0 else 0.1,
            "use_diversity_reward": True,
            "force_exploration": self.intervention_count > 0,
        }

    def on_intervention(self, score: float, gen: int, model, buffer):
        """触发干预"""
        self.intervention_count += 1
        print(f"[AntiCollapse] ⚠️  模式坍缩检测！触发干预 #{self.intervention_count}")
        print(f"[AntiCollapse] 策略：")
        print(f"  1. 重置 buffer 50% 旧样本")
        print(f"  2. 注入高强度噪声")
        print(f"  3. 强制高温探索")
        print(f"  4. 清空 n-gram 历史 30%")

        # 重置 buffer 一半
        if len(buffer) > 10:
            random.shuffle(buffer)
            removed = len(buffer) // 2
            del buffer[:removed]
            print(f"  → Buffer 减少 {removed} 个样本")

        # 清理 n-gram 历史
        if len(self.diversity.global_ngram_counts) > 100:
            items = list(self.diversity.global_ngram_counts.items())
            random.shuffle(items)
            keep = dict(items[:len(items) * 7 // 10])
            self.diversity.global_ngram_counts = Counter(keep)
            print(f"  → N-gram 历史减少 30%")

        # 注入新数据：让模型从"重启"开始
        print(f"  → 注入新种子文本（公网 Shakespeare 多样段落）")
        buffer.append("HAMLET:\nTo be, or not to be, that is the question:\nWhether 'tis nobler in the mind to suffer\n")
        buffer.append("PROSPERO:\nOur revels now are ended. These our actors,\nAs I foretold you, were all spirits and\n")
        buffer.append("LEAR:\nBlow, winds, and crack your cheeks! Rage! Blow!\nYou cataracts and hurricanoes, spout\n")

        # 强制下一阶段用高温
        self.annealer.base = 1.2

    def on_reset_needed(self, score: float, gen: int) -> bool:
        return self.resetter.should_reset(score, gen)
