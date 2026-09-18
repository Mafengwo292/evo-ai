"""
distributed/fleet.py
--------------------
异构算力抽象层。

把不同云（Modal / Vast.ai / Replicate / RunPod）抽象成统一的 `Worker` 接口。
coordinator 不用关心任务跑在哪里 —— 只需要 `submit(task)` 就行。

这是"分布式"的第一层：调度层解耦。
"""

from __future__ import annotations
import time
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum


class WorkerType(str, Enum):
    CPU_SMALL = "cpu_small"        # 适合评估、轻量任务
    CPU_LARGE = "cpu_large"
    GPU_T4 = "gpu_t4"              # 16GB VRAM, ~$0.5/h
    GPU_A10G = "gpu_a10g"          # 24GB VRAM, ~$1/h
    GPU_A100 = "gpu_a100"          # 40/80GB VRAM, ~$2-4/h
    GPU_H100 = "gpu_h100"          # 80GB VRAM, ~$2-8/h


@dataclass
class Worker:
    """一个远程算力节点"""
    worker_id: str
    worker_type: WorkerType
    region: str                   # 物理位置，如 "us-west", "eu-central", "asia-east"
    provider: str                 # "modal" / "vast" / "replicate" / "runpod"
    cost_per_hour: float          # 美元/小时
    is_busy: bool = False
    last_ping: float = field(default_factory=time.time)

    def score(self) -> float:
        """调度评分：便宜 + 空闲 + 离其他节点远（地理分布式）"""
        busy_penalty = 100.0 if self.is_busy else 0.0
        return self.cost_per_hour + busy_penalty


@dataclass
class Task:
    """一个训练/评估任务"""
    task_id: str
    task_type: str                # "train" / "evaluate" / "merge"
    payload: Dict                 # 任务参数（模型 config / 权重 URL 等）
    requirements: WorkerType
    submitted_at: float = field(default_factory=time.time)
    assigned_worker: Optional[str] = None
    result: Optional[Dict] = None
    status: str = "pending"       # pending / running / done / failed


class Fleet:
    """
    算力集群。
    真实实现会从 Modal / Vast / Replicate 的 API 拉取可用节点。
    W2 这里先 mock，但接口与真实一致。
    """

    def __init__(self):
        self.workers: List[Worker] = self._init_mock_fleet()
        self.tasks: List[Task] = []

    def _init_mock_fleet(self) -> List[Worker]:
        """Mock 一个跨地域的算力集群"""
        return [
            Worker("modal-a10g-1", WorkerType.GPU_A10G, "us-west", "modal", 1.0),
            Worker("modal-a100-1", WorkerType.GPU_A100, "us-east", "modal", 3.0),
            Worker("modal-h100-1", WorkerType.GPU_H100, "eu-west", "modal", 5.0),
            Worker("vast-t4-1",   WorkerType.GPU_T4,   "us-west", "vast",  0.4),
            Worker("vast-h100-1", WorkerType.GPU_H100, "asia-east", "vast", 2.0),
            Worker("replicate-cpu-1", WorkerType.CPU_LARGE, "us-east", "replicate", 0.2),
            Worker("runpod-a10g-1", WorkerType.GPU_A10G, "eu-central", "runpod", 0.8),
        ]

    def find_best_worker(self, requirement: WorkerType, prefer_region: str = None) -> Optional[Worker]:
        """挑一个最合适的 worker：满足类型 + 便宜 + 优先选指定区域"""
        candidates = [w for w in self.workers if w.worker_type == requirement and not w.is_busy]
        if not candidates:
            return None
        if prefer_region:
            same_region = [w for w in candidates if w.region == prefer_region]
            if same_region:
                candidates = same_region
        return min(candidates, key=lambda w: w.score())

    def submit(self, task: Task, prefer_region: str = None) -> bool:
        """提交任务到合适的 worker"""
        worker = self.find_best_worker(task.requirements, prefer_region)
        if worker is None:
            print(f"[Fleet] No available worker for {task.task_id} (need {task.requirements})")
            return False
        worker.is_busy = True
        task.assigned_worker = worker.worker_id
        task.status = "running"
        self.tasks.append(task)
        print(f"[Fleet] Task {task.task_id} -> {worker.provider}/{worker.worker_id} "
              f"({worker.worker_type.value}, {worker.region}, ${worker.cost_per_hour}/h)")
        return True

    def complete(self, task_id: str, result: Dict):
        """标记任务完成，释放 worker"""
        for task in self.tasks:
            if task.task_id == task_id:
                task.result = result
                task.status = "done"
                for w in self.workers:
                    if w.worker_id == task.assigned_worker:
                        w.is_busy = False
                print(f"[Fleet] Task {task.task_id} done. Result: {result.get('summary', '(no summary)')}")
                return
        print(f"[Fleet] Task {task_id} not found.")

    def status(self) -> Dict:
        return {
            "total_workers": len(self.workers),
            "busy_workers": sum(1 for w in self.workers if w.is_busy),
            "providers": list({w.provider for w in self.workers}),
            "regions": list({w.region for w in self.workers}),
            "pending_tasks": sum(1 for t in self.tasks if t.status == "pending"),
            "running_tasks": sum(1 for t in self.tasks if t.status == "running"),
            "done_tasks": sum(1 for t in self.tasks if t.status == "done"),
        }


def make_task_id(seed: str) -> str:
    return hashlib.md5(seed.encode()).hexdigest()[:8]
