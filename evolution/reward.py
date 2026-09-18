"""
evolution/reward.py
-------------------
Reward 函数：评估生成样本的质量。

W3 用启发式 reward（不依赖外部 LLM）：
- 长度合理性
- 多样性（不重复）
- 词汇丰富度
- 角色对话格式

W4 可以升级为 LLM-as-Judge（用 LLM 评估 LLM 的输出）。
"""

from __future__ import annotations
import re
import math
from collections import Counter
from typing import List


def heuristic_reward(text: str) -> float:
    """
    综合 reward：把多个启发式指标加权。
    返回 0~1 的分数。
    """
    if not text or len(text) < 10:
        return 0.0

    scores = {
        "length": _length_score(text),
        "diversity": _diversity_score(text),
        "format": _format_score(text),
        "coherence": _coherence_score(text),
    }
    weights = {
        "length": 0.2,
        "diversity": 0.3,
        "format": 0.2,
        "coherence": 0.3,
    }
    return sum(scores[k] * weights[k] for k in scores)


def _length_score(text: str) -> float:
    """长度合理：50~500 字符最佳"""
    n = len(text)
    if 50 <= n <= 500:
        return 1.0
    if n < 50:
        return n / 50.0
    if n > 500:
        return max(0.3, 1.0 - (n - 500) / 1000.0)
    return 0.5


def _diversity_score(text: str) -> float:
    """多样性：unique chars / total chars"""
    if not text:
        return 0.0
    return len(set(text)) / max(1, len(text))


def _format_score(text: str) -> float:
    """格式分：是否像角色对话（角色名 + 冒号 + 内容）"""
    # 检测 "NAME:\n..." 模式
    pattern = r"^[A-Z][A-Z\s]{2,20}:\s*\S"
    lines = [l for l in text.split("\n") if l.strip()]
    if not lines:
        return 0.0
    matches = sum(1 for l in lines if re.match(pattern, l))
    return min(1.0, matches / max(1, len(lines) // 2))


def _coherence_score(text: str) -> float:
    """连贯性：bigram 重复率越低越好"""
    words = text.lower().split()
    if len(words) < 4:
        return 0.5
    bigrams = [(words[i], words[i+1]) for i in range(len(words) - 1)]
    counter = Counter(bigrams)
    n_unique = len(counter)
    n_total = len(bigrams)
    return min(1.0, n_unique / n_total)


def reward_batch(samples: List[str]) -> List[float]:
    """批量评估"""
    return [heuristic_reward(s) for s in samples]
