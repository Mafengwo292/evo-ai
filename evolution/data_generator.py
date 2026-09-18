"""
evolution/data_generator.py
---------------------------
数据生成器：让模型自己造训练数据。

W3 默认 mock 模式：用一个"虚拟分布"模拟模型生成，节省算力。
真实模式：调用 W1 训练好的模型生成，或 Modal 部署的模型生成。
"""

from __future__ import annotations
import random
import os
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class GeneratedSample:
    prompt: str
    text: str
    reward: float = 0.0


# Shakespeare 风格角色名（用于 mock 生成）
MOCK_CHARACTERS = [
    "ROMEO", "JULIET", "HAMLET", "OPHELIA", "MACBETH", "LADY MACBETH",
    "KING RICHARD", "DUKE", "PROSPERO", "Ariel", "CALIBAN",
    "PORTIA", "SHYLOCK", "ANTONIO", "BASSANIO", "NERISSA",
    "HENRY", "HOTSPUR", "FALSTAFF", "GLOUCESTER",
]


MOCK_LINES = [
    "What light through yonder window breaks?",
    "It is the east, and Juliet is the sun.",
    "To be, or not to be, that is the question.",
    "All the world's a stage, and all the men and women merely players.",
    "Now is the winter of our discontent.",
    "Friends, Romans, countrymen, lend me your ears.",
    "The quality of mercy is not strain'd.",
    "Brevity is the soul of wit.",
    "There are more things in heaven and earth, Horatio, than are dreamt of in your philosophy.",
    "I am a man more sinn'd against than sinning.",
    "What's in a name? That which we call a rose by any other name would smell as sweet.",
    "Cowards die many times before their deaths; the valiant never taste of death but once.",
    "Some are born great, some achieve greatness, and some have greatness thrust upon them.",
    "If music be the food of love, play on.",
]


def mock_generate(prompt: str, model_quality: float = 0.5) -> str:
    """
    模拟模型生成。
    model_quality 越高，生成的文本越"合理"。
    """
    # 选 1-3 个角色对话
    n_chars = random.randint(1, 3) if model_quality < 0.7 else random.randint(2, 4)
    used_chars = random.sample(MOCK_CHARACTERS, n_chars)

    out_lines = []
    if prompt.strip() and random.random() < 0.4:
        out_lines.append(prompt.strip())

    for char in used_chars:
        n_lines = random.randint(1, 3)
        for _ in range(n_lines):
            if random.random() < model_quality:
                line = random.choice(MOCK_LINES)
            else:
                # 模拟"低质量"输出：随机字符
                line = "".join(random.choices("abcdefghijklmnop ", k=random.randint(5, 30)))
            out_lines.append(f"{char}:\n{line}")

    text = "\n\n".join(out_lines)

    # 模拟 model_quality 对格式的影响
    if model_quality < 0.4:
        # 模拟格式崩坏
        text = text.replace(":\n", " ").replace("\n\n", " ")

    return text


class DataGenerator:
    """
    数据生成器。W3 用 mock，W4 接真实模型。
    """

    def __init__(self, model_quality: float = 0.5, real_model = None):
        self.model_quality = model_quality
        self.real_model = real_model
        self.use_real = real_model is not None

    def generate(self, prompts: List[str], n_per_prompt: int = 4) -> List[GeneratedSample]:
        """从多个 prompt 各生成 n_per_prompt 个样本"""
        samples = []
        for prompt in prompts:
            for _ in range(n_per_prompt):
                if self.use_real:
                    text = self._real_generate(prompt)
                else:
                    text = mock_generate(prompt, self.model_quality)
                samples.append(GeneratedSample(prompt=prompt, text=text))
        return samples

    def _real_generate(self, prompt: str) -> str:
        """用真实模型生成（接口预留）"""
        # 真实环境会调 self.real_model.generate(...)
        return mock_generate(prompt, self.model_quality)
