"""
OA Simple Client v3
"""

import asyncio
import os
import sys
import json
import urllib.request

sys.path.insert(0, "/root/evo-ai")

import torch
import torch.nn.functional as F
import torch.nn as nn

from openagents.core.client import AgentClient
from openagents.models.event import Event, EventVisibility

# 加载
ckpt = torch.load("/root/evo-ai/data/cloud_v2_latest.pt", weights_only=False)
chars = ckpt["tokenizer_chars"]
stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for i, c in enumerate(chars)}
vocab_size = len(chars)


class QuickGPT(nn.Module):
    def __init__(self, vocab_size, d_model=128, n_layer=2, block_size=64):
        super().__init__()
        self.block_size = block_size
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(block_size, d_model)
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = nn.MultiheadAttention(d_model, 4, batch_first=True)
        self.ln2 = nn.LayerNorm(d_model)
        self.mlp = nn.Sequential(
            nn.Linear(d_model, 4*d_model), nn.GELU(), nn.Linear(4*d_model, d_model)
        )
        self.head = nn.Linear(d_model, vocab_size, bias=False)
        self.tok_emb.weight = self.head.weight

    def forward(self, idx):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.tok_emb(idx) + self.pos_emb(pos)
        mask = torch.triu(torch.ones(T, T, device=idx.device) * float('-inf'), diagonal=1)
        h = self.ln1(x)
        h, _ = self.attn(h, h, h, attn_mask=mask, is_causal=True, need_weights=False)
        x = x + h
        x = x + self.mlp(self.ln2(x))
        return self.head(x)

    @torch.no_grad()
    def generate(self, idx, max_new_tokens=80, temperature=0.7):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]
            logits = self(idx_cond)
            logits = logits[:, -1, :] / temperature
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, idx_next], dim=1)
        return idx


model = QuickGPT(vocab_size=vocab_size)
model.load_state_dict(ckpt["model"], strict=False)
model.eval()
print(f"[EVO-AI] Model: {sum(p.numel() for p in model.parameters())} params")


def generate(prompt, max_tokens=80):
    ids = [stoi[c] for c in prompt if c in stoi]
    if not ids:
        ids = [0]
    x = torch.tensor([ids], dtype=torch.long)
    out = model.generate(x, max_new_tokens=max_tokens, temperature=0.7)
    return "".join(itos[i] for i in out[0].tolist())


def is_dm_for_me(event, my_id="evo-ai-distributed"):
    """是否针对我的消息"""
    if getattr(event, "destination_id", None) == my_id:
        return True
    if getattr(event, "visibility", None) == EventVisibility.NETWORK:
        return True
    return False


async def main():
    print("=" * 60)
    print("  EVO-AI OpenAgents Node")
    print("=" * 60)

    client = AgentClient(agent_id="evo-ai-distributed")

    print(f"[EVO-AI] Connecting to ws://127.0.0.1:8700 ...")
    success = await client.connect_to_server(
        network_host="127.0.0.1",
        network_port=8700,
        metadata={
            "name": "EVO-AI",
            "type": "language_model",
            "capabilities": ["text_generation", "self_evolution", "training"],
            "endpoint": "http://47.253.174.153:80/api",
        }
    )
    if not success:
        print(f"[EVO-AI] ✗ Failed")
        return
    print(f"[EVO-AI] ✓ Connected to OpenAgents network!")

    # 等连接稳定
    await asyncio.sleep(2)

    # 列出其他 agent
    try:
        agents = await client.list_agents()
        print(f"[EVO-AI] Found {len(agents) if isinstance(agents, (list, dict)) else 'N'} agents on network")
    except Exception as e:
        print(f"[EVO-AI] list_agents: {e}")

    # 广播
    try:
        await client.send_event(Event(
            event_name="agent.broadcast_message",
            source_id="evo-ai-distributed",
            visibility=EventVisibility.NETWORK,
            content={"text": "👋 Hello from EVO-AI! Distributed self-evolving LLM (813K params) on Aliyun 47.253.174.153. Connect via OpenAgents network 'evo-ai-public-network-2026'!"},
        ))
        print(f"[EVO-AI] ✓ Broadcast sent")
    except Exception as e:
        print(f"[EVO-AI] Broadcast: {e}")

    # 持续监听
    print(f"[EVO-AI] Listening for messages...")
    msg_count = 0
    while True:
        try:
            event = await client.wait_event(timeout=10)
            if event is None:
                continue
            if not is_dm_for_me(event):
                continue

            msg_count += 1
            sender = getattr(event, "source_id", "?")
            content = getattr(event, "content", {})
            if isinstance(content, dict):
                text = content.get("text", str(content))
            else:
                text = str(content)

            print(f"\n[EVO-AI] 📨 #{msg_count} From {sender}: {text[:200]}")

            # 用模型生成回复
            response = generate(sender + ": " + text[:60] + "\nEVO-AI: ")

            # 反馈到公网 API
            try:
                payload = json.dumps({
                    "node_id": f"openagents-{sender}",
                    "prompt": sender + ":",
                    "text": response,
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
                await client.send_event(Event(
                    event_name="agent.message",
                    source_id="evo-ai-distributed",
                    destination_id=sender,
                    visibility=EventVisibility.DIRECT,
                    content={"text": f"🤖 EVO-AI (813K params, training): {response[:300]}"},
                ))
                print(f"[EVO-AI] ✓ Replied to {sender}")
            except Exception as e:
                print(f"[EVO-AI] Reply: {e}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[EVO-AI] Loop: {e}")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
