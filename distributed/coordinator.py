"""
distributed/coordinator.py
--------------------------
分布式自进化协调器（coordinator）。

这是整个系统的"调度大脑"：
1. 维护一群模型（种群）
2. 调度训练任务到 Fleet（跨互联网算力）
3. 从 WeightStore 拉取/推送权重
4. 评估 + 选择 + 变异 + 交叉
5. 推进世代

W2 的核心：训练任务漂在云端，coordinator 漂在你笔记本上（或另一台云上）。
W3 会加入：模型自生成数据。
"""

from __future__ import annotations
import os
import sys
import time
import random
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from distributed.fleet import Fleet, Task, WorkerType, make_task_id
from distributed.modal_trainer import submit_to_modal
from distributed.weight_store import WeightStore, WeightEntry


class DistributedCoordinator:
    """
    分布式自进化协调器。
    """

    def __init__(
        self,
        population_size: int = 4,
        base_config: Dict = None,
        store: WeightStore = None,
        fleet: Fleet = None,
    ):
        self.pop_size = population_size
        self.config = base_config or {
            "n_layer": 2,
            "d_model": 64,
            "n_head": 4,
            "block_size": 64,
            "vocab_size": 65,
        }
        self.store = store or WeightStore()
        self.fleet = fleet or Fleet()
        self.generation = 0
        self.population: List[str] = []   # 权重 id 列表
        self.history: List[Dict] = []

    def _make_individual(self, parent_id: Optional[str] = None) -> str:
        """
        生成一个新个体（训练任务 + 推送到仓库）。
        返回 weight_id。
        """
        # 1) 构造任务
        task_id = make_task_id(f"{self.generation}-{len(self.population)}-{time.time()}")
        task = Task(
            task_id=task_id,
            task_type="train",
            payload={
                "config": self.config,
                "parent_id": parent_id,
                "steps": 500,
            },
            requirements=WorkerType.GPU_A10G,   # 选 GPU 类型
        )
        # 2) 提交到 Fleet
        if not self.fleet.submit(task, prefer_region="us-west"):
            print(f"[Coordinator] Failed to submit task {task_id}")
            return None

        # 3) 模拟训练（真实环境会异步等待 Fleet 返回）
        result = submit_to_modal(task.payload)
        # 4) 标记 Fleet 任务完成
        self.fleet.complete(task_id, result)

        # 5) 推送到 WeightStore（用 store 已有 entry 数 + 1 保证唯一）
        weight_id = f"gen{self.generation}-ind{len(self.store.entries):03d}"
        # mock: 没有真实权重文件，用空路径
        weight_path = task.payload.get("_mock_weight_path", "") or "checkpoints/gpt_w1.pt"
        entry = self.store.push(
            weight_id=weight_id,
            weight_path=weight_path,
            parent_id=parent_id,
            generation=self.generation,
            metrics=result,
            tags=["modal-mock"] if not os.environ.get("MODAL_TOKEN_ID") else ["modal-real"],
        )
        return weight_id

    def _evaluate(self, weight_id: str) -> float:
        """评估一个个体（真实环境会从 WeightStore 拉权重 + 在 T4 上跑 benchmark）"""
        entry = self.store.pull(weight_id)
        if entry is None:
            return 0.0
        # mock: 用训练 loss 倒推一个分数
        loss = entry.metrics.get("final_loss", 4.0)
        score = max(0.0, 1.0 - loss / 4.0)   # loss 越低，分数越高
        return score

    def _select_and_reproduce(self) -> List[str]:
        """选择 + 繁殖新一代"""
        # 评估所有个体
        scores = [(wid, self._evaluate(wid)) for wid in self.population]
        scores.sort(key=lambda x: x[1], reverse=True)

        print(f"\n[Gen {self.generation}] Population fitness:")
        for wid, s in scores:
            entry = self.store.pull(wid)
            print(f"  {wid}: score={s:.3f}, loss={entry.metrics.get('final_loss', '?')}")

        # 选择 top 50% 作为父代
        n_survivors = max(1, self.pop_size // 2)
        survivors = [wid for wid, _ in scores[:n_survivors]]

        # 繁殖：每个 survivor 产生 2 个后代（变异）
        new_population = list(survivors)   # elitism：父代保留
        for parent in survivors:
            for _ in range(2):
                if len(new_population) >= self.pop_size:
                    break
                child_id = self._make_individual(parent_id=parent)
                if child_id:
                    new_population.append(child_id)

        return new_population[:self.pop_size]

    def evolve(self, n_generations: int = 5):
        """
        主循环：跑 N 代进化。
        """
        print("=" * 60)
        print(f"  Distributed Self-Evolving Coordinator")
        print(f"  Population: {self.pop_size}, Generations: {n_generations}")
        print("=" * 60)

        # 0) 初始化种群（第 0 代，从随机权重开始）
        print(f"\n[Init] Creating initial population of {self.pop_size}...")
        for i in range(self.pop_size):
            wid = self._make_individual(parent_id=None)
            if wid:
                self.population.append(wid)
            time.sleep(0.1)

        # 1) 进化循环
        for gen in range(n_generations):
            self.generation = gen
            print(f"\n{'='*60}")
            print(f"  Generation {gen}")
            print(f"{'='*60}")
            print(f"[Fleet] {self.fleet.status()}")

            self.population = self._select_and_reproduce()
            time.sleep(0.2)

        # 2) 总结
        print(f"\n{'='*60}")
        print(f"  Evolution Complete")
        print(f"{'='*60}")
        best = self.store.get_best(metric="final_loss", minimize=True)
        if best:
            print(f"Best individual: {best.weight_id}")
            print(f"  Generation: {best.generation}")
            print(f"  Final loss: {best.metrics.get('final_loss')}")
            print(f"  Parent: {best.parent_id}")

        # 打印 fleet 历史
        print(f"\n[Fleet Final] {self.fleet.status()}")
        print(f"[Store] Total weights stored: {len(self.store.entries)}")
