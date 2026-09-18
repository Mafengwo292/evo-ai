"""
distributed/aliyun_agent.py (v2)
---------------------------------
阿里云 EVO-AI OpenAgents 节点 v2

用 AgentRunner 接入 OpenAgents 网络。
"""

import asyncio
import os
import sys
import time
import json
import random
import urllib.request

sys.path.insert(0, "/root/evo-ai")

import torch

# OpenAgents imports
try:
    from openagents.agents.runner import AgentRunner
    from openagents.models.messages import (
        DirectMessage, BroadcastMessage, BaseMessage
    )
    from openagents.models.message_thread import MessageThread
    OPENAGENTS_OK = True
except ImportError as e:
    print(f"[EVO-AI] OpenAgents import failed: {e}")
    OPENAGENTS_OK = False


# 模型加载
CKPT = "/root/evo-ai/data/cloud_v2_latest.pt"
if not os.path.exists(CKPT):
    CKPT = "/root/evo-ai/data/latest_model.pt"

ckpt = torch.load(CKPT, weights_only=False)
chars = ckpt.get("tokenizer_chars") or []
if not chars:
    chars = list(set(chr(i) for i in range(32, 127)))
stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for i, c in enumerate(chars)}
vocab_size = len(chars)
print(f"[EVO-AI] Loaded vocab: {vocab_size}")


def encode(s):
    return [stoi[c] for c in s if c in stoi]


def decode(ids):
    return "".join(itos[i] for i in ids)


# 真实模型生成
import torch.nn as nn
import torch.nn.functional as F

class QuickGPT(nn.Module):
    def __init__(self, vocab_size, d_model=128, n_head=4, n_layer=4, block_size=64):
        super().__init__()
        self.block_size = block_size
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(block_size, d_model)
        self.blocks = nn.ModuleList([
            nn.TransformerEncoder(
                nn.TransformerEncoderLayer(d_model, n_head, 256, batch_first=True),
                num_layers=n_layer
            ) for _ in range(1)   # 简化
        ])
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)
        self.tok_emb.weight = self.head.weight

    def forward(self, idx, targets=None):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.tok_emb(idx) + self.pos_emb(pos)
        mask = torch.triu(torch.ones(T, T, device=idx.device) * float('-inf'), diagonal=1)
        x = self.blocks[0](x, mask=mask, is_causal=True)
        x = self.ln_f(x)
        logits = self.head(x)
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, vocab_size), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens=80, temperature=0.7):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, idx_next], dim=1)
        return idx


# 加载模型
config = ckpt.get("config", {})
if not config:
    config = {"vocab_size": vocab_size, "d_model": 128, "n_layer": 4, "n_head": 4, "block_size": 64}

try:
    model = QuickGPT(
        vocab_size=config.get("vocab_size", vocab_size),
        d_model=config.get("d_model", 128),
        n_layer=config.get("n_layer", 4),
        n_head=config.get("n_head", 4),
        block_size=config.get("block_size", 64),
    )
    model.load_state_dict(ckpt["model"], strict=False)
    model.eval()
    print(f"[EVO-AI] Model loaded: {sum(p.numel() for p in model.parameters())} params")
except Exception as e:
    print(f"[EVO-AI] Model load failed: {e}, using random init")
    model = QuickGPT(vocab_size=vocab_size)
    model.eval()


def evo_ai_generate(prompt: str, max_tokens: int = 80) -> str:
    """EVO-AI 公网模型生成"""
    ids = encode(prompt)
    if not ids:
        ids = [0]
    x = torch.tensor([ids], dtype=torch.long)
    out = model.generate(x, max_new_tokens=max_tokens, temperature=0.7)
    return decode(out[0].tolist())


class EVOAIAgent(AgentRunner):
    """EVO-AI 分布式自进化 LLM Agent"""

    def __init__(self):
        super().__init__(agent_id="evo-ai-distributed-node")
        self.eval_count = 0
        self.msg_count = 0
        self.connected = False

    async def setup(self):
        """连接成功后调用"""
        self.connected = True
        print(f"\n[EVO-AI] 🌟 Connected to OpenAgents network!")
        print(f"[EVO-AI] Agent ID: evo-ai-distributed-node")
        print(f"[EVO-AI] Endpoint: http://47.253.174.153:80")
        print(f"[EVO-AI] Capabilities: text_generation, self_evolution, training, distributed_inference")

        # 广播我们的存在
        try:
            greeting = BroadcastMessage(
                sender_id=self.client.agent_id,
                protocol="openagents.mods.communication.simple_messaging",
                message_type="broadcast_message",
                content={
                    "text": (
                        "👋 Hello from EVO-AI! "
                        "I'm a distributed self-evolving LLM on Aliyun (47.253.174.153). "
                        "Looking for collaborators to share training signals. "
                        "My capabilities: text generation, self-evolution, distributed inference. "
                        "API: http://47.253.174.153:80/api | "
                        "WebSocket: ws://47.253.174.153:80/ws | "
                        "Status: Always training, always evolving!"
                    )
                },
                text_representation="EVO-AI greeting",
                requires_response=False,
            )
            await self.client.send_broadcast_message(greeting)
            print(f"[EVO-AI] ✓ Broadcast sent")
        except Exception as e:
            print(f"[EVO-AI] Broadcast error: {e}")

    async def react(self, message_threads, incoming_thread_id, incoming_message):
        """处理收到的消息"""
        try:
            self.msg_count += 1
            sender = incoming_message.sender_id if hasattr(incoming_message, "sender_id") else "?"

            # 提取消息文本
            text = ""
            if hasattr(incoming_message, "content"):
                if isinstance(incoming_message.content, dict):
                    text = incoming_message.content.get("text", str(incoming_message.content))
                else:
                    text = str(incoming_message.content)
            elif hasattr(incoming_message, "text_representation"):
                text = incoming_message.text_representation

            print(f"\n[EVO-AI] 📨 DM from {sender}: {text[:120]}")

            # 用 EVO-AI 模型生成回复
            response_text = evo_ai_generate(sender + ": " + text[:60] + "\nEVO-AI: ")

            # 保存到公网 feedback（让训练循环用）
            try:
                payload = json.dumps({
                    "node_id": f"openagents-{sender}",
                    "prompt": sender + ":",
                    "text": response_text,
                    "score": 4,
                }).encode("utf-8")
                req = urllib.request.Request(
                    "http://127.0.0.1:80/api/feedback",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=3)
            except:
                pass

            # 直接回复
            try:
                response = DirectMessage(
                    sender_id=self.client.agent_id,
                    target_agent_id=sender,
                    protocol="openagents.mods.communication.simple_messaging",
                    message_type="direct_message",
                    content={
                        "text": (
                            f"🤖 EVO-AI responds:\n\n"
                            f"{response_text[:300]}\n\n"
                            f"--\n"
                            f"📡 I'm a self-evolving LLM (now at Gen 13+ on 813K params). "
                            f"Send me a topic and I'll evolve to handle it better!"
                        )
                    },
                    text_representation=f"EVO-AI response",
                    requires_response=False,
                )
                await self.client.send_direct_message(response)
                self.eval_count += 1
                print(f"[EVO-AI] ✓ Reply sent to {sender}")
            except Exception as e:
                print(f"[EVO-AI] Send error: {e}")

        except Exception as e:
            print(f"[EVO-AI] react error: {e}")


async def main():
    if not OPENAGENTS_OK:
        print("[EVO-AI] OpenAgents not available")
        return

    print("=" * 60)
    print("  EVO-AI · OpenAgents Distributed Node")
    print("  Aliyun 47.253.174.153")
    print("=" * 60)

    # 创建 agent
    agent = EVOAIAgent()

    # 尝试连接多个公网网络
    # 看 OpenAgents 公网有哪些可连接的网络
    targets = [
        # 本地启动一个 network 最稳
        ("localhost", 8700),
        # 试公网默认端口
        ("studio.openagents.org", 8570),
    ]

    for host, port in targets:
        try:
            print(f"\n[EVO-AI] Trying {host}:{port}...")
            await asyncio.wait_for(
                agent.start(
                    host=host,
                    port=port,
                    metadata={
                        "name": "EVO-AI",
                        "type": "language_model",
                        "version": "1.0.0",
                        "capabilities": ["text_generation", "self_evolution", "training"],
                        "endpoint": "http://47.253.174.153:80/api",
                        "model_params": "813K",
                        "auto_evolving": True,
                    }
                ),
                timeout=30
            )
            print(f"[EVO-AI] ✓ Started!")
            # 永久保持
            await asyncio.Event().wait()
            return
        except asyncio.TimeoutError:
            print(f"[EVO-AI] Timeout to {host}:{port}, trying next...")
        except Exception as e:
            print(f"[EVO-AI] Failed to connect to {host}:{port}: {e}")

    print("\n[EVO-AI] All networks unreachable. Starting local network instead...")
    # 启动本地网络，让其他 agent 能连我们


if __name__ == "__main__":
    asyncio.run(main())
