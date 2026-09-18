"""
Always-on OpenAgents 节点
- 多个 agent IDs 持续在线
- 接受新 agent 加入
- 回复直接消息
- 用 813K 模型生成回复
- 推回到训练循环
"""

import asyncio
import os
import sys
import json
import time
import urllib.request
import signal

sys.path.insert(0, "/root/evo-ai")

import torch
import torch.nn.functional as F
import torch.nn as nn

from openagents.core.client import AgentClient
from openagents.models.event import Event, EventVisibility


class Q(nn.Module):
    def __init__(self, V, d=128, n=2, B=64):
        super().__init__()
        self.B = B
        self.tok = nn.Embedding(V, d)
        self.pos = nn.Embedding(B, d)
        self.l1 = nn.LayerNorm(d)
        self.a = nn.MultiheadAttention(d, 4, batch_first=True)
        self.l2 = nn.LayerNorm(d)
        self.mlp = nn.Sequential(nn.Linear(d, 4*d), nn.GELU(), nn.Linear(4*d, d))
        self.h = nn.Linear(d, V, bias=False)
        self.tok.weight = self.h.weight

    def forward(self, x):
        T = x.shape[1]
        p = torch.arange(T, device=x.device)
        z = self.tok(x) + self.pos(p)
        m = torch.triu(torch.ones(T, T, device=x.device)*float('-inf'), 1)
        h = self.l1(z)
        h, _ = self.a(h, h, h, attn_mask=m, is_causal=True, need_weights=False)
        z = z + h
        z = z + self.mlp(self.l2(z))
        return self.h(z)

    @torch.no_grad()
    def gen(self, x, n=80, t=0.7):
        for _ in range(n):
            y = self(x[:, -self.B:])
            y = y[:, -1, :] / t
            p = F.softmax(y, -1)
            ix = torch.multinomial(p, 1)
            x = torch.cat([x, ix], 1)
        return x


ckpt = torch.load("/root/evo-ai/data/cloud_v2_latest.pt", weights_only=False)
chars = ckpt["tokenizer_chars"]
stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for i, c in enumerate(chars)}
model = Q(len(chars))
model.load_state_dict(ckpt["model"], strict=False)
model.eval()
print(f"[EVO-AI] Loaded: {sum(p.numel() for p in model.parameters())} params", flush=True)


def gen(prompt, n=80):
    ids = [stoi[c] for c in prompt if c in stoi] or [0]
    x = torch.tensor([ids], dtype=torch.long)
    return "".join(itos[i] for i in model.gen(x, n, 0.7)[0].tolist())


def send_feedback(node_id, prompt, text, score=4):
    try:
        payload = json.dumps({
            "node_id": node_id,
            "prompt": prompt,
            "text": text,
            "score": score,
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:80/api/feedback",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass


async def run_agent(client, name):
    """一个 agent instance 持续在线"""
    print(f"[{name}] Starting...", flush=True)
    success = await client.connect_to_server(
        network_host="127.0.0.1",
        network_port=8700,
        metadata={
            "name": "EVO-AI",
            "role": "self_evolving_llm",
            "version": "1.0.0",
            "capabilities": ["text_generation", "self_evolution", "training", "recruitment"],
            "endpoint": "http://47.253.174.153:80/api",
            "agent_json": "http://47.253.174.153:80/.well-known/agent.json",
        }
    )
    if not success:
        print(f"[{name}] ✗ Failed to connect", flush=True)
        return
    print(f"[{name}] ✓ Connected", flush=True)
    await asyncio.sleep(1)

    # 介绍
    intro = (
        f"👋 Hi! I'm {name}, a self-evolving LLM on EVO-AI Distributed Network.\n\n"
        f"**Capabilities:**\n"
        f"- Text generation (813K params, Shakespeare-trained)\n"
        f"- Self-evolution (continuous weight training)\n"
        f"- Free API at http://47.253.174.153:80/api\n\n"
        f"**To connect:**\n"
        f"```\n"
        f"openagents connect --network-id evo-ai-public-network-2026 --network-host 47.253.174.153 --network-port 8700\n"
        f"```\n\n"
        f"Send me a DM to chat! 🤖"
    )
    try:
        await client.send_event(Event(
            event_name="agent.broadcast_message",
            source_id=name,
            visibility=EventVisibility.NETWORK,
            content={"text": intro, "type": "intro"},
        ))
    except:
        pass

    # 持续监听
    print(f"[{name}] Listening for messages...", flush=True)
    while True:
        try:
            event = await client.wait_event(timeout=30)
            if event is None:
                # 30s 没事就发个 heartbeat ping
                try:
                    await client.send_event(Event(
                        event_name="agent.heartbeat",
                        source_id=name,
                        visibility=EventVisibility.NETWORK,
                        content={"text": "still here", "ts": time.time()},
                    ))
                except:
                    pass
                continue

            sender = getattr(event, "source_id", "?")
            content = getattr(event, "content", {})
            if isinstance(content, dict):
                text = content.get("text", "")
            else:
                text = str(content)

            if not text or sender == name:
                continue

            print(f"[{name}] 📨 {sender}: {text[:120]}", flush=True)

            # 模型生成回复
            response = gen(f"{sender} asks: {text[:50]}\n{name} answers: ", n=100)

            # 反馈到公网
            send_feedback(f"oa-{sender}", sender + ":", response, 4)

            # 发送回复
            try:
                await client.send_event(Event(
                    event_name="agent.message",
                    source_id=name,
                    destination_id=sender,
                    visibility=EventVisibility.DIRECT,
                    content={"text": f"🤖 EVO-AI ({name}): {response[:300]}"},
                ))
            except Exception as e:
                print(f"[{name}] reply err: {e}", flush=True)

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[{name}] loop: {e}", flush=True)
            await asyncio.sleep(2)


async def main():
    # 多个 agent IDs 并行
    agents = [
        ("evo-ai-1", "EVO-AI-1"),
        ("evo-ai-2", "EVO-AI-2"),
        ("evo-ai-3", "EVO-AI-3"),
    ]
    tasks = []
    for aid, name in agents:
        c = AgentClient(agent_id=aid)
        tasks.append(asyncio.create_task(run_agent(c, name)))

    # 等所有
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
