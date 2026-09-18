"""
core/memory.py
--------------
两段式记忆系统：
- 短期记忆：当前会话最近 N 条对话（ring buffer）
- 长期记忆：历史高评分对话，存到 JSONL 文件，每次对话后 dump 一次

W2 会把长期记忆升级到向量数据库（ChromaDB / FAISS）做语义检索。
"""

from __future__ import annotations
import json
import os
from collections import deque
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Turn:
    """一轮对话"""
    role: str              # "user" / "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    feedback: Optional[int] = None   # 1 = 👍, -1 = 👎, 0 = 中性, None = 未反馈
    score: float = 0.0              # 综合评分（会被进化引擎更新）


class Memory:
    def __init__(
        self,
        short_term_capacity: int = 20,
        long_term_top_k: int = 50,
        long_term_path: str = "data/long_term_memory.jsonl",
    ):
        self.short_term: deque[Turn] = deque(maxlen=short_term_capacity)
        self.long_term: List[Turn] = []
        self.long_term_path = long_term_path
        self.long_term_top_k = long_term_top_k
        self._load_long_term()

    def _load_long_term(self):
        """启动时加载历史长期记忆"""
        if not os.path.exists(self.long_term_path):
            return
        with open(self.long_term_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                self.long_term.append(Turn(**d))
        # 按 score 排序
        self.long_term.sort(key=lambda t: t.score, reverse=True)
        print(f"[Memory] Loaded {len(self.long_term)} long-term turns.")

    def add_turn(self, role: str, content: str, feedback: Optional[int] = None):
        t = Turn(role=role, content=content, feedback=feedback)
        self.short_term.append(t)
        if feedback is not None:
            self.long_term.append(t)
            self._persist_long_term()

    def update_last_feedback(self, feedback: int):
        """更新最后一轮 assistant 回复的反馈"""
        for t in reversed(self.short_term):
            if t.role == "assistant":
                t.feedback = feedback
                t.score = float(feedback)
                # 同步到长期记忆
                self.long_term.append(t)
                self._persist_long_term()
                return
        print("[Memory] No assistant turn to update.")

    def get_context_messages(self, include_long_term: bool = True) -> List[Dict[str, str]]:
        """
        组装给 LLM 的消息列表：
        - 短期记忆全部
        - 长期记忆里评分最高的几条作为"参考先例"
        """
        messages: List[Dict[str, str]] = []

        if include_long_term and self.long_term:
            # 取 top_k 高分历史对话作为先例
            top_examples = self.long_term[:3]
            example_texts = []
            for t in top_examples:
                if t.feedback == 1 and t.role == "assistant":
                    example_texts.append(f"（用户曾满意）{t.content[:200]}")
            if example_texts:
                messages.append({
                    "role": "system",
                    "content": "你过去让用户满意的回答范例：\n" + "\n---\n".join(example_texts),
                })

        for t in self.short_term:
            messages.append({"role": t.role, "content": t.content})
        return messages

    def _persist_long_term(self):
        """长期记忆写回文件"""
        os.makedirs(os.path.dirname(self.long_term_path), exist_ok=True)
        with open(self.long_term_path, "w", encoding="utf-8") as f:
            for t in self.long_term[-self.long_term_top_k:]:
                f.write(json.dumps(asdict(t), ensure_ascii=False) + "\n")
