"""
distributed/aliyun_network.py
------------------------------
阿里云 OpenAgents Network Host

让 EVO-AI 作为 OpenAgents 网络的 host（47.253.174.153:8700），
任何 agent 都能 connect 到这个公网网络。

这是真正的"分布式节点 + 公网协作"：EVO-AI 不再是孤岛，
而是一个开放的 agent 网络，承载多个智能体协同进化。
"""

import asyncio
import os
import sys
import time
import json
import urllib.request

sys.path.insert(0, "/root/evo-ai")

# 准备一个 network 配置
NETWORK_DIR = "/root/evo-ai/data/oa_network"
os.makedirs(NETWORK_DIR, exist_ok=True)

# 写一个 network.yaml
import yaml

network_config = {
    "network": {
        "name": "EVO-AI Distributed Network",
        "mode": "centralized",
        "transport": "websocket",
        "host": "0.0.0.0",
        "port": 8700,
        "discovery_enabled": True,
        "encryption_enabled": False,
    },
    "network_profile": {
        "discoverable": True,
        "name": "EVO-AI Distributed Self-Evolving LLM",
        "description": "A public OpenAgents network hosted by EVO-AI. Connect to share training signals, models, and collaborate on distributed self-evolution.",
        "tags": ["llm", "self-evolving", "distributed", "openagents", "public"],
        "capacity": 100,
        "network_id": "evo-ai-public-network-2026",
    },
    "mods": [
        {"name": "openagents.mods.communication.simple_messaging", "enabled": True},
        {"name": "openagents.mods.discovery.agent_discovery", "enabled": True},
    ],
}

with open(os.path.join(NETWORK_DIR, "network.yaml"), "w") as f:
    yaml.dump(network_config, f, default_flow_style=False)

print(f"[EVO-AI Network] Config written to {NETWORK_DIR}/network.yaml")
print(f"[EVO-AI Network] Network ID: evo-ai-public-network-2026")
print(f"[EVO-AI Network] Will host on 0.0.0.0:8700")
print()

# 用 openagents 命令启动
# openagents network start /path/to/network.yaml

cmd = f"cd {NETWORK_DIR} && /root/miniconda/envs/evo/bin/openagents network start {NETWORK_DIR}/network.yaml --host 0.0.0.0 --port 8700"
print(f"[EVO-AI Network] Command: {cmd}")
print()

# 在 tmux 里启动
import subprocess
subprocess.Popen([
    "tmux", "new-session", "-d", "-s", "oa-network",
    cmd
])

# 等几秒看 log
time.sleep(10)

# 检查状态
log_path = f"{NETWORK_DIR}/network.log"
if os.path.exists(log_path):
    with open(log_path) as f:
        print(f.read()[:2000])
else:
    print(f"[EVO-AI Network] No log at {log_path}")
    # 看 tmux 输出
    r = subprocess.run(["tmux", "capture-pane", "-t", "oa-network", "-p"], capture_output=True, text=True)
    print(r.stdout[:2000])

# 测试连接
print()
print("=" * 60)
print("Testing connection...")
try:
    req = urllib.request.Request("http://127.0.0.1:8700/")
    resp = urllib.request.urlopen(req, timeout=5)
    print(f"✓ Network reachable: HTTP {resp.status}")
    print(f"  Content preview: {resp.read()[:200]}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
