"""
model/transformer.py
--------------------
最基础的 Transformer block。
从零实现，不调用任何高级 API。
参考: "Attention Is All You Need" (Vaswani et al., 2017)
       + nanoGPT (Karpathy, 2022)
"""

from __future__ import annotations
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class CausalSelfAttention(nn.Module):
    """因果自注意力（Causal = 只能看到过去）"""

    def __init__(self, d_model: int, n_heads: int, block_size: int, dropout: float = 0.0):
        super().__init__()
        assert d_model % n_heads == 0
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        self.qkv = nn.Linear(d_model, 3 * d_model, bias=False)
        self.out_proj = nn.Linear(d_model, d_model, bias=False)
        self.dropout = dropout
        # 预注册 causal mask（避免每次重新生成）
        mask = torch.tril(torch.ones(block_size, block_size)).view(1, 1, block_size, block_size)
        self.register_buffer("mask", mask)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C = x.shape
        # 1) QKV 一起算
        qkv = self.qkv(x)   # (B, T, 3C)
        q, k, v = qkv.chunk(3, dim=-1)
        # 2) 分头
        q = q.view(B, T, self.n_heads, self.d_head).transpose(1, 2)  # (B, H, T, D)
        k = k.view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        v = v.view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        # 3) Attention
        att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(self.d_head))   # (B, H, T, T)
        att = att.masked_fill(self.mask[:, :, :T, :T] == 0, float("-inf"))
        att = F.softmax(att, dim=-1)
        att = F.dropout(att, p=self.dropout, training=self.training)
        # 4) 加权求和 + 输出投影
        y = att @ v   # (B, H, T, D)
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        return self.out_proj(y)


class MLP(nn.Module):
    """FFN: 两层全连接 + GELU"""

    def __init__(self, d_model: int, dropout: float = 0.0):
        super().__init__()
        self.fc = nn.Linear(d_model, 4 * d_model, bias=False)
        self.proj = nn.Linear(4 * d_model, d_model, bias=False)
        self.dropout = dropout

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.dropout(self.proj(F.gelu(self.fc(x))), p=self.dropout, training=self.training)


class Block(nn.Module):
    """一个 Transformer block: Pre-Norm + Attention + MLP，残差连接"""

    def __init__(self, d_model: int, n_heads: int, block_size: int, dropout: float = 0.0):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, n_heads, block_size, dropout)
        self.ln2 = nn.LayerNorm(d_model)
        self.mlp = MLP(d_model, dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x
