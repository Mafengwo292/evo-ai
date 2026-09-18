"""
evolution/self_reward.py
------------------------
内部 reward 函数：模型自我评估，不依赖任何外部信号。

真正的"自进化" = 不需要人类打分、不需要外部 LLM、不需要用户反馈。
模型自己知道什么好、什么不好。

核心机制：
- Self-Consistency：多次采样一致性 → 模型"有把握"的程度
- Diversity：token 级熵 → 鼓励多样性
- Format Match：是否匹配训练分布
- Perplexity Improvement：新数据在当前模型下的困惑度
- Novelty：与已有 buffer 的差异度（避免重复）
"""

from __future__ import annotations
import math
import random
import re
from collections import Counter
from typing import List, Dict, Optional, Callable
import torch
import torch.nn.functional as F


# ============================================================
# 1. Self-Consistency Reward
# ============================================================

def self_consistency_reward(
    text: str,
    generate_fn: Callable[[str, int], List[str]],
    prompt: str,
    n_samples: int = 3,
) -> float:
    """
    多次生成同 prompt 的样本，计算一致性。
    一致性越高 = 模型越"有把握" = 越好。
    """
    samples = generate_fn(prompt, n_samples)
    if len(samples) < 2:
        return 0.5
    # 用 n-gram 重叠率衡量一致性
    n = 3
    all_ngrams = []
    for s in samples:
        words = s.lower().split()
        ngs = set(tuple(words[i:i+n]) for i in range(len(words) - n + 1))
        all_ngrams.append(ngs)
    # 计算 pairwise Jaccard 相似度
    if not all_ngrams:
        return 0.5
    intersections = []
    unions = []
    for i in range(len(all_ngrams)):
        for j in range(i+1, len(all_ngrams)):
            intersections.append(len(all_ngrams[i] & all_ngrams[j]))
            unions.append(len(all_ngrams[i] | all_ngrams[j]))
    if not unions or all(u == 0 for u in unions):
        return 0.5
    jaccard = sum(intersections) / sum(unions)
    return min(1.0, jaccard * 2)   # 放大


# ============================================================
# 2. Diversity Reward
# ============================================================

def diversity_reward(text: str) -> float:
    """
    Token 级多样性。
    鼓励模型生成多样、不重复的内容。
    """
    if not text or len(text) < 10:
        return 0.0
    chars = list(text)
    if not chars:
        return 0.0
    # 字符级 unique ratio
    char_unique = len(set(chars)) / len(chars)

    # 词级 unique ratio
    words = text.split()
    if len(words) < 2:
        return char_unique
    word_unique = len(set(words)) / len(words)

    # bigram 重复率（越低越好）
    bigrams = [(words[i], words[i+1]) for i in range(len(words) - 1)]
    if not bigrams:
        return word_unique
    bigram_unique = len(set(bigrams)) / len(bigrams)

    return (char_unique + word_unique + bigram_unique) / 3


# ============================================================
# 3. Format Match Reward
# ============================================================

def format_match_reward(text: str, target_format: str = "shakespeare_dialogue") -> float:
    """
    格式匹配度：是否符合训练数据分布。
    """
    if target_format == "shakespeare_dialogue":
        return _shakespeare_format_score(text)
    return 0.5


def _shakespeare_format_score(text: str) -> float:
    """评估是否像莎士比亚对话"""
    # 检测 "NAME:\n..." 模式
    pattern = r"^[A-Z][A-Z\s]{1,20}:\s*\S"
    lines = [l for l in text.split("\n") if l.strip()]
    if not lines:
        return 0.0
    matches = sum(1 for l in lines if re.match(pattern, l))
    return min(1.0, matches / max(1, len(lines) // 2))


# ============================================================
# 4. Perplexity Reward
# ============================================================

def perplexity_reward(text: str, model, tokenizer, block_size: int) -> float:
    """
    模型对这段文本的困惑度。
    perplexity 越低 = 模型"懂"这段文本 = 越好。
    """
    if not text or len(text) < 5:
        return 0.0
    try:
        ids = tokenizer.encode(text)[:block_size]
        if len(ids) < 2:
            return 0.0
        x = torch.tensor([ids[:-1]], dtype=torch.long)
        y = torch.tensor([ids[1:]], dtype=torch.long)
        with torch.no_grad():
            _, loss = model(x, y)
        # loss 在 1.0-5.0 范围内
        # 转换为 0-1 reward（loss 越低 reward 越高）
        reward = max(0.0, 1.0 - (loss.item() - 1.0) / 4.0)
        return reward
    except Exception:
        return 0.5


# ============================================================
# 5. Novelty Reward
# ============================================================

def novelty_reward(text: str, existing_buffer: List[str], threshold: float = 0.6) -> float:
    """
    新颖度：与已有 buffer 的最大相似度越低越好。
    鼓励新东西，避免模式坍缩。
    """
    if not existing_buffer:
        return 1.0
    text_ngrams = _get_ngrams(text.lower(), n=3)
    if not text_ngrams:
        return 0.5
    max_sim = 0.0
    for existing in existing_buffer[-50:]:   # 只对比最近 50 个
        existing_ngrams = _get_ngrams(existing.lower(), n=3)
        if not existing_ngrams:
            continue
        sim = len(text_ngrams & existing_ngrams) / max(1, len(text_ngrams | existing_ngrams))
        max_sim = max(max_sim, sim)
    # 相似度越低，reward 越高
    return 1.0 - min(1.0, max_sim * 1.5)


def _get_ngrams(text: str, n: int = 3) -> set:
    words = text.split()
    return set(tuple(words[i:i+n]) for i in range(len(words) - n + 1))


# ============================================================
# 6. Combined Self-Reward
# ============================================================

class SelfReward:
    """
    内部 reward 组合器。
    把多个 self-reward 加权得到最终分数。
    """

    def __init__(
        self,
        model=None,
        tokenizer=None,
        block_size: int = 32,
        weights: Optional[Dict[str, float]] = None,
        target_format: str = "shakespeare_dialogue",
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.block_size = block_size
        self.target_format = target_format
        self.weights = weights or {
            "consistency": 0.20,
            "diversity": 0.20,
            "format": 0.20,
            "perplexity": 0.25,
            "novelty": 0.15,
        }
        self.buffer: List[str] = []

    def add_to_buffer(self, text: str):
        self.buffer.append(text)
        if len(self.buffer) > 500:
            self.buffer = self.buffer[-500:]

    def score(self, text: str, prompt: str = "") -> float:
        """
        综合 reward。
        """
        rewards = {
            "diversity": diversity_reward(text),
            "format": format_match_reward(text, self.target_format),
            "novelty": novelty_reward(text, self.buffer),
            "consistency": 0.5,   # 默认值，batch 模式跳过单样本评估
        }

        if self.model is not None and self.tokenizer is not None:
            rewards["perplexity"] = perplexity_reward(
                text, self.model, self.tokenizer, self.block_size
            )
        else:
            rewards["perplexity"] = 0.5

        total = sum(rewards[k] * self.weights[k] for k in self.weights)
        return total

    def score_batch(self, samples: List[Dict]) -> List[float]:
        """批量评估 [(prompt, text), ...]"""
        scores = []
        for s in samples:
            score = self.score(s["text"], s.get("prompt", ""))
            scores.append(score)
            self.add_to_buffer(s["text"])
        return scores
