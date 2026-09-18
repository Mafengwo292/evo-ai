"""
evolution/population.py
-----------------------
多种群管理 + 模型融合（Evolutionary Model Merging）。

W4 stub：定义接口，真实实现在 W4 完成。

核心思想：
- 不只训练一个模型，训练一群（种群）
- 每个世代：选择 + 交叉（权重融合）+ 变异
- 这是 Sakana AI 的核心算法
"""

from __future__ import annotations
import os
import sys
import random
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class MergedIndividual:
    """一个融合后的个体"""
    weight_id: str
    parent_ids: List[str]
    merge_weights: List[float]      # 融合权重
    fitness: float = 0.0
    generation: int = 0


class EvolutionaryMerger:
    """
    进化式模型融合器（W4 stub）。
    用 Sakana AI 的思想：多个模型 + 进化算法找最优融合权重。
    """

    def __init__(self, n_merge: int = 3, sigma: float = 0.15):
        self.n_merge = n_merge
        self.sigma = sigma
        self.population: List[MergedIndividual] = []

    def merge_state_dicts(
        self,
        state_dicts: List[Dict[str, torch.Tensor]],
        weights: List[float],
    ) -> Dict[str, torch.Tensor]:
        """
        线性加权融合多个 state_dict。
        merged = sum(weight_i * state_dict_i)
        """
        assert len(state_dicts) == len(weights)
        # 归一化
        s = sum(weights)
        weights = [w / s for w in weights] if s > 0 else [1.0 / len(weights)] * len(weights)

        merged = {}
        for key in state_dicts[0].keys():
            tensors = [sd[key].float() * w for sd, w in zip(state_dicts, weights)]
            merged[key] = sum(tensors).to(state_dicts[0][key].dtype)
        return merged

    def propose_merges(
        self,
        candidate_state_dicts: List[Dict[str, torch.Tensor]],
        n_proposals: int = 5,
    ) -> List[MergedIndividual]:
        """提出 N 个候选融合方案"""
        proposals = []
        for i in range(n_proposals):
            # 随机选 n_merge 个父模型
            n = min(self.n_merge, len(candidate_state_dicts))
            parents = random.sample(range(len(candidate_state_dicts)), n)
            weights = [random.gauss(1.0 / n, self.sigma) for _ in range(n)]
            weights = [max(0.0, w) for w in weights]
            proposals.append(MergedIndividual(
                weight_id=f"merge_{i}_{'-'.join(map(str, parents))}",
                parent_ids=[f"parent_{p}" for p in parents],
                merge_weights=weights,
                generation=0,
            ))
        return proposals

    def evaluate(self, individual: MergedIndividual, eval_fn) -> float:
        """评估一个融合方案"""
        individual.fitness = eval_fn(individual)
        return individual.fitness


# 简化：W4 暂用 mock state_dict
def mock_state_dict(seed: int) -> Dict[str, torch.Tensor]:
    torch.manual_seed(seed)
    return {
        "w1": torch.randn(64, 64),
        "w2": torch.randn(64, 64),
    }
