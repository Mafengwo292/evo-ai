"""
model/gpt.py
------------
完整的 nanoGPT：embedding + N x Block + final LN + LM head
"""

from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F
from .transformer import Block


class GPTConfig:
    """超参数配置（写死一个 nanoGPT 默认值，W2 会从 yaml 读）"""
    block_size: int = 256       # 上下文窗口
    vocab_size: int = 65        # Tiny Shakespeare 字符数
    n_layer: int = 6            # Transformer block 数
    n_head: int = 6             # 注意力头数
    d_model: int = 192          # 隐层维度
    dropout: float = 0.0


class GPT(nn.Module):
    def __init__(self, config: GPTConfig):
        super().__init__()
        self.config = config
        # token + position embedding
        self.tok_emb = nn.Embedding(config.vocab_size, config.d_model)
        self.pos_emb = nn.Embedding(config.block_size, config.d_model)
        self.drop = nn.Dropout(config.dropout)
        # Transformer blocks
        self.blocks = nn.ModuleList([
            Block(config.d_model, config.n_head, config.block_size, config.dropout)
            for _ in range(config.n_layer)
        ])
        # final layer norm
        self.ln_f = nn.LayerNorm(config.d_model)
        # LM head: 从隐层到 vocab
        self.head = nn.Linear(config.d_model, config.vocab_size, bias=False)
        # 权重共享：embedding 和 head 共享权重（nanoGPT 风格，能省参数）
        self.tok_emb.weight = self.head.weight

        # 初始化
        self._init_weights()

    def _init_weights(self):
        """标准初始化（接近 GPT-2 风格）"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, mean=0.0, std=0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Embedding):
                nn.init.normal_(m.weight, mean=0.0, std=0.02)

    def forward(self, idx: torch.Tensor, targets: torch.Tensor = None):
        """
        idx: (B, T) token id
        targets: (B, T) 训练时的目标 token id
        """
        B, T = idx.shape
        assert T <= self.config.block_size

        pos = torch.arange(0, T, dtype=torch.long, device=idx.device)
        tok_emb = self.tok_emb(idx)       # (B, T, C)
        pos_emb = self.pos_emb(pos)       # (T, C)
        x = self.drop(tok_emb + pos_emb)

        for block in self.blocks:
            x = block(x)
        x = self.ln_f(x)
        logits = self.head(x)             # (B, T, vocab_size)

        loss = None
        if targets is not None:
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                targets.view(-1),
            )
        return logits, loss

    @torch.no_grad()
    def generate(self, idx: torch.Tensor, max_new_tokens: int, temperature: float = 1.0,
                 top_k: int = None) -> torch.Tensor:
        """自回归生成"""
        for _ in range(max_new_tokens):
            # 截断到 block_size
            idx_cond = idx if idx.size(1) <= self.config.block_size else idx[:, -self.config.block_size:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature
            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = -float("inf")
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, idx_next], dim=1)
        return idx

    def num_params(self) -> int:
        return sum(p.numel() for p in self.parameters())
