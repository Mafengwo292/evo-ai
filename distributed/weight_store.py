"""
distributed/weight_store.py
----------------------------
模型权重"仓库"。

在真实分布式系统中，模型权重不存放在本地，而是放在共享仓库里。
各 worker 从仓库拉初始权重，训练完推回仓库。

W2 实现：HuggingFace Hub 风格接口（可对接 HF Hub / S3 / GCS / 自建 MinIO）。
W2 默认 mock 存本地 data/weights/。
"""

from __future__ import annotations
import os
import json
import time
import shutil
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class WeightEntry:
    """一条权重记录"""
    weight_id: str
    parent_id: Optional[str]            # 从哪个权重进化而来
    generation: int                    # 第几代
    metrics: Dict                      # 训练/评估指标
    weight_path: str                   # 实际权重文件路径（mock 时为本地）
    url: str = ""                      # 真实仓库 URL
    created_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)


class WeightStore:
    """
    模型权重仓库。
    真实实现会 push / pull 到 HuggingFace Hub。
    W2 默认存本地。
    """

    def __init__(self, local_dir: str = "data/weights"):
        self.local_dir = local_dir
        self.entries: Dict[str, WeightEntry] = {}
        os.makedirs(local_dir, exist_ok=True)
        self._load_index()

    def _load_index(self):
        idx_path = os.path.join(self.local_dir, "index.json")
        if os.path.exists(idx_path):
            with open(idx_path, "r") as f:
                data = json.load(f)
                for e in data.get("entries", []):
                    self.entries[e["weight_id"]] = WeightEntry(**e)

    def _save_index(self):
        idx_path = os.path.join(self.local_dir, "index.json")
        with open(idx_path, "w") as f:
            json.dump({
                "entries": [asdict(e) for e in self.entries.values()],
            }, f, indent=2)

    def push(self, weight_id: str, weight_path: str, parent_id: Optional[str],
             generation: int, metrics: Dict, tags: List[str] = None) -> WeightEntry:
        """把训练好的权重推入仓库"""
        # mock: 复制到本地仓库
        dest = os.path.join(self.local_dir, f"{weight_id}.pt")
        if os.path.exists(weight_path):
            shutil.copy(weight_path, dest)
        entry = WeightEntry(
            weight_id=weight_id,
            parent_id=parent_id,
            generation=generation,
            metrics=metrics,
            weight_path=dest,
            tags=tags or [],
        )
        # 真实环境会 push 到 HF Hub
        # entry.url = hf_hub_upload(...)
        self.entries[weight_id] = entry
        self._save_index()
        print(f"[WeightStore] Pushed {weight_id} (gen {generation}, loss={metrics.get('final_loss', '?')})")
        return entry

    def get_latest(self) -> Optional[WeightEntry]:
        if not self.entries:
            return None
        return max(self.entries.values(), key=lambda e: e.generation)

    def get_best(self, metric: str = "final_loss", minimize: bool = True) -> Optional[WeightEntry]:
        """按指标取最优权重"""
        if not self.entries:
            return None
        valid = [e for e in self.entries.values() if metric in e.metrics]
        if not valid:
            return None
        return min(valid, key=lambda e: e.metrics[metric]) if minimize else max(valid, key=lambda e: e.metrics[metric])

    def get_history(self) -> List[WeightEntry]:
        return sorted(self.entries.values(), key=lambda e: e.generation)

    def pull(self, weight_id: str) -> Optional[WeightEntry]:
        """从仓库拉取权重（真实环境会从 HF Hub 下载）"""
        return self.entries.get(weight_id)
