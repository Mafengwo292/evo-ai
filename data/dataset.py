"""
data/dataset.py
---------------
数据加载 + 字符级 tokenizer。

W1 用 Tiny Shakespeare（约 1MB 文本，Karpathy 经典 demo 数据集）。
代码会自动下载。如果网络不通，可手动放到 data/tinyshakespeare.txt。
"""

from __future__ import annotations
import os
import urllib.request
import torch
from torch.utils.data import Dataset


DATA_URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
DATA_PATH = "data/tinyshakespeare.txt"


def download_tinyshakespeare():
    if not os.path.exists(DATA_PATH):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        print(f"[Data] Downloading Tiny Shakespeare to {DATA_PATH} ...")
        urllib.request.urlretrieve(DATA_URL, DATA_PATH)
    return DATA_PATH


class CharTokenizer:
    """字符级 tokenizer"""

    def __init__(self, text: str):
        chars = sorted(list(set(text)))
        self.vocab_size = len(chars)
        self.stoi = {ch: i for i, ch in enumerate(chars)}
        self.itos = {i: ch for i, ch in enumerate(chars)}

    def encode(self, s: str) -> list[int]:
        return [self.stoi[c] for c in s if c in self.stoi]

    def decode(self, ids: list[int]) -> str:
        return "".join([self.itos[i] for i in ids])


class TextDataset(Dataset):
    """滑动窗口式数据集"""

    def __init__(self, token_ids: list[int], block_size: int):
        self.data = torch.tensor(token_ids, dtype=torch.long)
        self.block_size = block_size

    def __len__(self):
        return len(self.data) - self.block_size

    def __getitem__(self, idx):
        x = self.data[idx : idx + self.block_size]
        y = self.data[idx + 1 : idx + 1 + self.block_size]
        return x, y


def prepare_data(block_size: int = 256, train_ratio: float = 0.9):
    """返回 (train_ds, val_ds, tokenizer)"""
    path = download_tinyshakespeare()
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    print(f"[Data] Loaded {len(text)} chars from {path}")

    tok = CharTokenizer(text)
    print(f"[Data] Vocab size: {tok.vocab_size}")

    ids = tok.encode(text)
    n = len(ids)
    split = int(n * train_ratio)
    train_ids, val_ids = ids[:split], ids[split:]

    train_ds = TextDataset(train_ids, block_size)
    val_ds = TextDataset(val_ids, block_size)
    print(f"[Data] Train: {len(train_ds)} samples, Val: {len(val_ds)} samples")
    return train_ds, val_ds, tok
