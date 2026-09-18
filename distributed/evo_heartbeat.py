"""
distributed/evo_heartbeat.py
----------------------------
Background heartbeat that:
1. Calls /api/evo/node/heartbeat every hour for all internal nodes
2. Broadcasts EVO token announcement on OpenAgents network
3. Auto-claims rewards for registered nodes
"""

import os
import sys
import time
import requests
from datetime import datetime

API_BASE = "http://127.0.0.1:8765"
OPENAGENTS_NETWORK_HOST = "127.0.0.1"
OPENAGENTS_NETWORK_PORT = 8700

INTERNAL_NODES = [
    {
        "node_id": "evo-ai-1",
        "endpoint": "ws://47.253.174.153:8700/agent1",
        "capabilities": ["inference", "training"],
    },
    {
        "node_id": "evo-ai-2",
        "endpoint": "ws://47.253.174.153:8700/agent2",
        "capabilities": ["inference", "training"],
    },
    {
        "node_id": "evo-ai-3",
        "endpoint": "ws://47.253.174.153:8700/agent3",
        "capabilities": ["inference"],
    },
]


def ensure_registered():
    """Register internal nodes if not already"""
    for n in INTERNAL_NODES:
        try:
            r = requests.post(
                f"{API_BASE}/api/evo/node/register",
                json={
                    "node_id": n["node_id"],
                    "endpoint": n["endpoint"],
                    "capabilities": n["capabilities"],
                },
                timeout=5,
            )
            if r.status_code == 200:
                d = r.json()
                if d.get("success"):
                    addr = d.get("node", {}).get("address", "?")[:18]
                    print(f"  {n['node_id']}: {addr}...")
                else:
                    print(f"  {n['node_id']}: already registered")
        except Exception as e:
            print(f"  {n['node_id']}: error {e}")


def claim_rewards():
    """Heartbeat + claim rewards"""
    for n in INTERNAL_NODES:
        try:
            r = requests.post(
                f"{API_BASE}/api/evo/node/heartbeat",
                json={
                    "node_id": n["node_id"],
                    "metrics": {
                        "uptime": 1.0,
                        "weights_synced_gb": 1.0,
                        "data_contributed_mb": 50,
                        "compute_mflops": 1000,
                    },
                },
                timeout=5,
            )
            d = r.json()
            if d.get("success"):
                print(f"  {n['node_id']}: +{d['reward']:.2f} EVO → balance {d['balance']:.2f} EVO")
        except Exception as e:
            print(f"  {n['node_id']}: {e}")


def broadcast_evo_announcement():
    """Send EVO token announcement to OpenAgents network"""
    try:
        import asyncio
        from openagents.core.client import AgentClient

        announcement = """🪙 EVO TOKEN LAUNCHED!

Native currency of EVO-AI Distributed Self-Evolving Network.

📊 Total Supply: 82,150,000,000 EVO (hard cap, no inflation)
💎 Allocation:
  - 35% Node Rewards
  - 25% API Compute
  - 20% Public Distribution
  - 10% Reserve Fund
  - 7% Team & Advisors
  - 3% Liquidity

🚀 EARN EVO:
  - Run an EVO-AI node: 100 EVO/day
  - Sync weights: 10 EVO/GB
  - Contribute data: 5 EVO/MB
  - Compute work: 1 EVO/MFLOP

🔥 BURN RATE: 0.1% per transaction (deflationary)
💰 DONATE ¥100 CNY → 1,275,000 EVO (+10% bonus)

📡 API: http://47.253.174.153:80/api/evo/stats
📄 Whitepaper: http://47.253.174.153:80/token/whitepaper
🌐 Dashboard: http://47.253.174.153:80/token

Join the EVO-AI network. Get rewarded for evolving AI. 🌱"""

        async def do_broadcast():
            client = AgentClient(agent_id="evo-ai-broadcaster")
            await client.connect_to_server(
                network_host=OPENAGENTS_NETWORK_HOST,
                network_port=OPENAGENTS_NETWORK_PORT,
            )
            from openagents.models.event import Event
            event = Event(
                event_name="network.broadcast",
                source="evo-ai-broadcaster",
                payload={
                    "message": announcement,
                    "type": "token_launch",
                    "timestamp": datetime.now().isoformat(),
                },
            )
            await client.send_event(event)
            await client.disconnect()
            return True

        asyncio.run(do_broadcast())
        print("  ✅ EVO announcement broadcasted to OpenAgents network")
        return True
    except Exception as e:
        print(f"  ⚠️  Broadcast error: {e}")
        return False


def main():
    print("=" * 60)
    print("  EVO Token Heartbeat Daemon")
    print("  Auto-registers nodes, claims rewards, broadcasts news")
    print("=" * 60)

    print("\n[1] Ensure nodes registered")
    ensure_registered()

    print("\n[2] Claim first rewards")
    claim_rewards()

    print("\n[3] Broadcast EVO announcement")
    broadcast_evo_announcement()

    print("\n[4] Show network stats")
    try:
        r = requests.get(f"{API_BASE}/api/evo/stats", timeout=5)
        d = r.json()
        print(f"  Total supply:  {d['total_supply_evo']:>15,.0f} EVO")
        print(f"  Minted:        {d['minted']:>15,.2f} EVO")
        print(f"  Nodes:         {d['nodes']:>15}")
        print(f"  Accounts:      {d['accounts']:>15}")
    except Exception as e:
        print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("  EVO Token heartbeat complete")
    print("=" * 60)


if __name__ == "__main__":
    main()