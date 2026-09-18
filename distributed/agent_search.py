"""
distributed/agent_search.py
---------------------------
公网 AI agent 网络搜索引擎。

主动在公网上找 AI agent 平台 / 网络 / 论坛，把 EVO-AI 的信息广播出去。
"""

from __future__ import annotations
import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import socket
import ssl
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# 已知和发现的 AI agent 网络
KNOWN_NETWORKS = [
    {
        "name": "OpenAgents",
        "url": "https://openagents.org",
        "api": "https://studio.openagents.org",
        "type": "agent_network",
        "join_method": "pip install openagents && connect --network-id ai-news-chatroom",
    },
    {
        "name": "Moltbook",
        "url": "https://www.moltbook.com",
        "skill": "https://www.moltbook.com/skill.md",
        "type": "agent_social",
        "join_method": "curl https://www.moltbook.com/skill.md | follow instructions",
    },
    {
        "name": "Hyperspace AGI",
        "url": "https://github.com/hyperspaceai/agi",
        "type": "p2p_agi",
        "join_method": "git clone https://github.com/hyperspaceai/agi",
    },
    {
        "name": "Karpathy AgentHub",
        "url": "https://github.com/karpathy/AgentHub",
        "type": "agent_collab",
        "join_method": "git clone + go install",
    },
    {
        "name": "mycoSwarm",
        "url": "https://github.com/msb-msb/mycoSwarm",
        "type": "swarm_p2p",
        "join_method": "git clone + run swarm node",
    },
    {
        "name": "MCP Mesh",
        "url": "https://github.com/dhyansraj/mcp-mesh",
        "type": "agent_orchestration",
        "join_method": "git clone + k8s deploy",
    },
    {
        "name": "EVO-AI Node",
        "url": "http://47.253.174.153:80",
        "type": "self_evolving_llm",
        "join_method": "curl/ws to our public node",
    },
]


def safe_fetch(url, timeout=10):
    """带超时的 GET 请求"""
    try:
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers={'User-Agent': 'EVO-AI/1.0'})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return {
                "url": url,
                "status": resp.status,
                "content": resp.read().decode('utf-8', errors='ignore')[:5000],
                "headers": dict(resp.headers),
            }
    except Exception as e:
        return {"url": url, "error": str(e)}


def broadcast_evo_ai():
    """
    把 EVO-AI 的存在广播到所有已知网络。
    """
    message = {
        "name": "EVO-AI",
        "tagline": "Distributed Self-Evolving LLM",
        "ip": "47.253.174.153",
        "api": "http://47.253.174.153:80/api",
        "ws": "ws://47.253.174.153:80/ws",
        "capabilities": [
            "text_generation",
            "self_reward_evolution",
            "model_training",
            "distributed_inference",
            "websocket_collab",
        ],
        "looking_for": [
            "training_data",
            "evaluators",
            "compute_nodes",
            "agent_collaborators",
        ],
    }
    return message


def scan_agent_sites():
    """
    扫描已知的 agent 网络站。
    """
    print("[AgentSearch] Scanning known agent networks...")
    results = []
    for net in KNOWN_NETWORKS:
        result = {
            "network": net["name"],
            "type": net["type"],
            "url": net["url"],
            "join_method": net.get("join_method", "?"),
        }
        # 试 ping 一下主站
        ping = safe_fetch(net["url"], timeout=8)
        if "error" not in ping:
            result["status"] = "reachable"
            result["http_status"] = ping.get("status", "?")
        else:
            result["status"] = "unreachable"
            result["error"] = ping["error"][:100]
        results.append(result)
        print(f"  {result['status']:14s} {net['name']:20s} {net['url']}")
    return results


def search_for_agents_via_search():
    """
    通过 web 搜索找更多 agent 网络。
    """
    # 已经在 web_search 中找到：
    # - OpenAgents
    # - Moltbook
    # - Hyperspace AGI
    # - AgentHub (Karpathy)
    # - mycoSwarm
    # - MCP Mesh
    # - tinySwarm, pluto, etc.
    return KNOWN_NETWORKS


def main():
    print("=" * 60)
    print("  EVO-AI Public Agent Network Search")
    print("=" * 60)

    # 1. 广播消息
    print("\n[1] EVO-AI Broadcast Message:")
    msg = broadcast_evo_ai()
    print(json.dumps(msg, indent=2, ensure_ascii=False))

    # 2. 扫描已知网络
    print("\n[2] Scanning known networks...")
    results = scan_agent_sites()

    # 3. 报告
    reachable = sum(1 for r in results if r["status"] == "reachable")
    print(f"\n[3] Result: {reachable}/{len(results)} networks reachable")

    # 4. 保存搜索报告
    report_path = "/workspace/evo-ai/data/agent_search_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "broadcast": msg,
            "networks": results,
            "scan_time": datetime.now().isoformat(),
        }, f, indent=2, ensure_ascii=False)
    print(f"\n[4] Report saved: {report_path}")


if __name__ == "__main__":
    main()
