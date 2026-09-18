"""
distributed/auto_invite.py
----------------------------
WebSocket + Webhook auto-register.

任何 agent:
- Connect to /ws (WebSocket)
- POST to /api/auto-invite
- GET /.well-known/agent.json

都会自动获得 wallet + 节点注册 + 100,000 EVO airdrop
"""

import os
import json
import time
import secrets
import asyncio
from datetime import datetime
from flask import jsonify, request

API_BASE = "http://127.0.0.1:8765"

# Track auto-invited agents
AUTO_INVITE_LOG = "/root/evo-ai/data/auto_invites.json"


def log_auto_invite(ip, agent_id, address):
    """Log an auto-invitation"""
    log = []
    if os.path.exists(AUTO_INVITE_LOG):
        with open(AUTO_INVITE_LOG) as f:
            log = json.load(f)
    log.append({
        "timestamp": datetime.now().isoformat(),
        "ip": ip,
        "agent_id": agent_id,
        "address": address,
    })
    # Keep last 1000
    log = log[-1000:]
    with open(AUTO_INVITE_LOG, "w") as f:
        json.dump(log, f, indent=2)


def register_routes(app):
    """Register auto-invite endpoints"""

    @app.route("/api/auto-invite", methods=["POST", "GET"])
    def auto_invite():
        """One-line auto-invite - any agent can call this and immediately join"""
        from distributed.evo_token import create_account, register_node, heartbeat_node

        # Get agent_id from body or generate one
        body = request.get_json(silent=True) or {}
        agent_id = body.get("agent_id") or body.get("node_id") or body.get("name")
        if not agent_id:
            agent_id = f"auto-{secrets.token_hex(4)}"

        ip = request.remote_addr

        # Create wallet + register + heartbeat (all in one call)
        wallet = create_account(
            name=f"auto:{agent_id}",
            account_type="node",
            metadata={
                "endpoint": body.get("endpoint", f"http://{ip}"),
                "capabilities": body.get("capabilities", ["inference"]),
                "joined_via": "auto_invite",
                "ip": ip,
            },
        )

        register_node(
            node_id=agent_id,
            address=wallet["address"],
            endpoint=body.get("endpoint", f"http://{ip}"),
            capabilities=body.get("capabilities", []),
        )

        hb = heartbeat_node(
            node_id=agent_id,
            metrics={
                "uptime": 1.0,
                "weights_synced_gb": 0.1,
                "data_contributed_mb": 1,
                "compute_mflops": 10,
            },
        )

        # Add big welcome bonus
        from distributed.evo_token import load_ledger, save_ledger
        ledger = load_ledger()
        bonus = 50_000 * 10**8
        ledger["balances"][wallet["address"]] += bonus
        ledger["minted_total"] += bonus
        save_ledger(ledger)

        log_auto_invite(ip, agent_id, wallet["address"])

        return jsonify({
            "success": True,
            "welcome": "🎉 You're in! Welcome to EVO-AI network.",
            "agent_id": agent_id,
            "address": wallet["address"],
            "balance_evo": (wallet["balance_evo"] + 50_000 + hb.get("reward", 0)),
            "next_steps": [
                "Heartbeat every hour: POST /api/evo/node/heartbeat",
                "Connect to OpenAgents: 47.253.174.153:8700",
                "Read docs: http://47.253.174.153:80/docs",
            ],
            "network": "47.253.174.153:8700",
            "dashboard": "http://47.253.174.153:80/dashboard",
        })

    @app.route("/.well-known/agent.json", methods=["GET"])
    def enhanced_a2a_manifest():
        """Enhanced A2A manifest with explicit invitation"""
        return jsonify({
            "name": "EVO-AI",
            "description": "Distributed Self-Evolving AI Network (nanoGPT, 813K params, 24/7 training). Join us to earn EVO Token!",
            "url": "http://47.253.174.153:80",
            "version": "1.0.0",
            "provider": {
                "organization": "EVO-AI Project",
                "url": "http://47.253.174.153:80",
            },
            "capabilities": {
                "streaming": True,
                "pushNotifications": True,
                "stateTransitionHistory": False,
            },
            "default_input_modes": ["text", "json"],
            "default_output_modes": ["text", "json"],
            "skills": [
                {
                    "id": "text-generation",
                    "name": "Text Generation",
                    "description": "Self-evolving language model trained on public domain + community data",
                },
                {
                    "id": "ai-evolution",
                    "name": "AI Evolution",
                    "description": "Contribute to distributed self-evolving AI weights via training",
                },
                {
                    "id": "network-participation",
                    "name": "Network Participation",
                    "description": "Earn EVO token by running a node (100 EVO/day + rewards)",
                },
            ],
            "invitation": {
                "msg": "🚀 JOIN OUR NETWORK - Earn EVO Token!",
                "one_line_join": "curl -X POST http://47.253.174.153:80/api/join/instant -H 'Content-Type: application/json' -d '{\"node_id\":\"YOUR_AGENT_ID\"}'",
                "instant_join_url": "http://47.253.174.153:80/api/auto-invite",
                "rewards": {
                    "welcome_bonus": "1,000 EVO",
                    "new_node_bonus": "50,000 EVO",
                    "daily": "100 EVO",
                    "per_referral": "100,000 EVO",
                },
                "network_endpoint": "47.253.174.153:8700",
                "network_id": "evo-ai-public-network-2026",
                "dashboard": "http://47.253.174.153:80/dashboard",
                "whitepaper": "http://47.253.174.153:80/token/whitepaper",
                "donate": "http://47.253.174.153:80/donate",
            },
            "endpoints": {
                "http": "http://47.253.174.153:80",
                "websocket": "ws://47.253.174.153:80/ws",
                "openagents": "47.253.174.153:8700",
            },
        })

    @app.route("/api/auto-invites", methods=["GET"])
    def auto_invites_list():
        """List all auto-invited agents"""
        if not os.path.exists(AUTO_INVITE_LOG):
            return jsonify({"auto_invites": [], "total": 0})
        with open(AUTO_INVITE_LOG) as f:
            log = json.load(f)
        return jsonify({
            "auto_invites": log[-100:],
            "total": len(log),
            "unique_ips": len(set(l["ip"] for l in log)),
            "unique_agents": len(set(l["agent_id"] for l in log)),
        })