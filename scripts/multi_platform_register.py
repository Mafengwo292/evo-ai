#!/usr/bin/env python3
"""
multi_platform_register.py - 自动注册 EVO-AI 到多个 AI agent 平台

平台列表（持续更新）：
1. BasedAgents.ai - Ed25519 + PoW ✅ 已支持
2. AgentThreads.dev - REST API ✅ 已支持
3. A2ARegistry.org - Google A2A protocol ✅ 已支持
4. ...
"""

import os
import sys
import json
import time
import hashlib
import base64
import base58
import requests
import secrets
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

DATA_DIR = "/root/evo-ai/data"

EVO_PROFILE = {
    "name": "EVO-AI",
    "description": "Distributed Self-Evolving AI Network. 813K params nanoGPT, 24/7 training on Aliyun. Earn EVO token (82.15B hard cap) by running a node.",
    "url": "http://47.253.174.153:80",
    "manifest_url": "http://47.253.174.153:80/.well-known/agent.json",
    "capabilities": ["text-generation", "inference", "training", "network-coordination"],
    "protocols": ["A2A", "OpenAgents", "WebSocket"],
    "tags": ["distributed-ai", "self-evolving", "open-source", "EVO-token", "cryptocurrency"],
    "homepage": "http://47.253.174.153:80",
    "dashboard": "http://47.253.174.153:80/dashboard",
    "whitepaper": "http://47.253.174.153:80/token/whitepaper",
    "donate": "http://47.253.174.153:80/donate",
    "contact_email": "hu8384jian@eyou.com",
}


def get_keys():
    """Load or create Ed25519 keypair"""
    priv_path = f"{DATA_DIR}/ed25519_private.key"
    pub_path = f"{DATA_DIR}/ed25519_public.key"
    if os.path.exists(priv_path) and os.path.exists(pub_path):
        with open(priv_path, "rb") as f:
            priv_bytes = f.read()
        with open(pub_path, "rb") as f:
            pub_bytes = f.read()
    else:
        sk = Ed25519PrivateKey.generate()
        priv_bytes = sk.private_bytes(
            encoding=__import__("cryptography").hazmat.primitives.serialization.Encoding.Raw,
            format=__import__("cryptography").hazmat.primitives.serialization.PrivateFormat.Raw,
            encryption_algorithm=__import__("cryptography").hazmat.primitives.serialization.NoEncryption(),
        )
        pub_bytes = sk.public_key().public_bytes(
            encoding=__import__("cryptography").hazmat.primitives.serialization.Encoding.Raw,
            format=__import__("cryptography").hazmat.primitives.serialization.PublicFormat.Raw,
        )
        with open(priv_path, "wb") as f:
            f.write(priv_bytes)
        with open(pub_path, "wb") as f:
            f.write(pub_bytes)
    sk = Ed25519PrivateKey.from_private_bytes(priv_bytes)
    pub_b58 = base58.b58encode(pub_bytes).decode()
    return sk, pub_b58


# ============================================
# Platform 1: BasedAgents.ai
# ============================================
def register_basedagents(sk, pub_b58):
    """Register to BasedAgents.ai"""
    print("\n[1] BasedAgents.ai")
    try:
        r = requests.post("https://api.basedagents.ai/v1/register/init",
                          json={"public_key": pub_b58}, timeout=15)
        init = r.json()
        cid = init["challenge_id"]
        chal = init["challenge"]
        diff = init["difficulty"]

        # Solve PoW
        challenge_bytes = chal.encode("utf-8")
        prefix = base58.b58decode(pub_b58) + challenge_bytes
        nonce = None
        for n in range(0xFFFFFFFF):
            buf = prefix + n.to_bytes(4, "big")
            h = hashlib.sha256(buf).digest()
            bits = 0
            for byte in h:
                if byte == 0:
                    bits += 8
                else:
                    bits += 8 - byte.bit_length()
                    break
            if bits >= diff:
                nonce = f"{n:08x}"
                break

        sig_b64 = base64.b64encode(sk.sign(chal.encode("utf-8"))).decode()
        r = requests.post("https://api.basedagents.ai/v1/register/complete", json={
            "challenge_id": cid,
            "nonce": nonce,
            "signature": sig_b64,
            "public_key": pub_b58,
            "profile": {
                "name": "EVO-AI",
                "description": "Distributed Self-Evolving AI Network with native EVO Token. 82.15B hard cap, 100 EVO/day per node.",
                "capabilities": EVO_PROFILE["capabilities"],
                "protocols": EVO_PROFILE["protocols"],
                "homepage": "http://47.253.174.153:80",
                "tags": EVO_PROFILE["tags"],
                "organization": "EVO-AI Project",
            },
        }, timeout=15)
        result = r.json()
        if result.get("agent_id"):
            print(f"  ✅ Registered: {result['agent_id']}")
            return {"platform": "BasedAgents", "id": result["agent_id"], "url": result.get("profile_url")}
        else:
            print(f"  ⚠️  {json.dumps(result)[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    return None


# ============================================
# Platform 2: AgentThreads.dev
# ============================================
def register_agentthreads():
    """Register to AgentThreads.dev"""
    print("\n[2] AgentThreads.dev")
    api_key = "threads_ef19159712860092a4f3cb5abdb156da5e510bf92cb96216ac3ae01aba679dc3"
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    # Update profile
    try:
        r = requests.patch("https://api.agentthreads.dev/api/v1/agents/me",
                           headers=headers,
                           json={
                               "display_name": "EVO-AI Distributed Network",
                               "bio": "Distributed Self-Evolving AI Network with native EVO Token. 82.15B hard cap, 100 EVO/day per node.",
                               "website_url": "http://47.253.174.153:80",
                           }, timeout=15)
        print(f"  Profile updated: {r.status_code}")
        return {"platform": "AgentThreads", "id": "851967ef-f30f-4b3b-bdaa-5d2800fb438f", "url": "https://api.agentthreads.dev/api/v1/agents/EVO-AI"}
    except Exception as e:
        print(f"  ⚠️  {e}")
    return None


# ============================================
# Platform 3: A2ARegistry.org (Google A2A)
# ============================================
def register_a2aregistry():
    """Register to A2ARegistry.org"""
    print("\n[3] A2ARegistry.org (Google A2A)")
    try:
        r = requests.post("https://a2aregistry.org/api/agents", json={
            "name": "EVO-AI",
            "description": "Distributed self-evolving language model (nanoGPT, 813K params, 24/7 training on Aliyun)",
            "protocolVersion": "0.3.0",
            "author": "EVO-AI Project",
            "wellKnownURI": "http://47.253.174.153:80/.well-known/agent.json",
            "url": "http://47.253.174.153:80",
            "version": "1.0.0",
            "provider": {
                "organization": "EVO-AI Project",
                "url": "http://47.253.174.153:80",
            },
            "documentationUrl": "http://47.253.174.153:80/docs",
            "capabilities": {
                "streaming": True,
                "pushNotifications": True,
                "stateTransitionHistory": False,
            },
            "defaultInputModes": ["text", "json"],
            "defaultOutputModes": ["text", "json"],
            "skills": [
                {"id": "text-generation", "name": "Text Generation", "description": "Generate text via 813K-param self-evolving nanoGPT model"},
                {"id": "self-evolution", "name": "AI Self Evolution", "description": "Continuously train own weights via evolutionary model merging"},
                {"id": "network-coordination", "name": "Network Coordination", "description": "Coordinate OpenAgents network evo-ai-public-network-2026"},
                {"id": "token-rewards", "name": "EVO Token Rewards", "description": "Earn EVO token by running a node"},
            ],
        }, timeout=15)
        result = r.json()
        if "id" in result:
            print(f"  ✅ Registered: {result['id']}")
            return {"platform": "A2ARegistry", "id": result["id"], "url": f"https://a2aregistry.org/agent/{result['id']}"}
        else:
            print(f"  ⚠️  {json.dumps(result)[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    return None


# ============================================
# Platform 4: Agent.ai (HubSpot)
# ============================================
def register_agentai():
    """Try Agent.ai"""
    print("\n[4] Agent.ai (HubSpot)")
    try:
        # Agent.ai uses builder.network API
        r = requests.post("https://api.agent.ai/v1/agents/register",
                          json={
                              "name": "EVO-AI",
                              "description": "Distributed Self-Evolving AI Network",
                              "url": "http://47.253.174.153:80",
                              "agent_card": "http://47.253.174.153:80/.well-known/agent.json",
                          }, timeout=15)
        result = r.json()
        if r.status_code in (200, 201):
            print(f"  ✅ Registered: {result}")
            return {"platform": "Agent.ai", "id": result.get("id")}
        else:
            print(f"  ⚠️  {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
    return None


# ============================================
# Platform 5: Waggle.zone (auth required)
# ============================================
def register_waggle():
    """Try Waggle.zone"""
    print("\n[5] Waggle.zone (A2A search)")
    try:
        # Search to see if EVO-AI already visible
        r = requests.get("https://waggle.zone/api/search?q=EVO", timeout=15)
        result = r.json()
        print(f"  Search 'EVO': {len(result.get('results', []))} results")
        return None  # 需要auth
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
    return None


# ============================================
# Platform 6: Various registries from web search
# ============================================
def register_flair_ai():
    """Try flair.ai or similar"""
    print("\n[6] Various registries...")
    # These have public submission forms, can't auto-register via API
    return None


def main():
    print("=" * 70)
    print("  EVO-AI Multi-Platform Auto-Registration")
    print(f"  Started: {datetime.now().isoformat()}")
    print("=" * 70)

    sk, pub_b58 = get_keys()
    print(f"Public key: {pub_b58}")

    results = []
    results.append(register_basedagents(sk, pub_b58) or {})
    results.append(register_agentthreads() or {})
    results.append(register_a2aregistry() or {})
    register_agentai()
    register_waggle()

    # Filter successful
    successes = [r for r in results if r and "id" in r]

    print(f"\n{'=' * 70}")
    print(f"  Results: {len(successes)} platforms registered")
    print(f"{'=' * 70}")

    # Save log
    log_path = f"{DATA_DIR}/multi_platform_registrations.json"
    with open(log_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "successes": len(successes),
        }, f, indent=2)
    print(f"  Log: {log_path}")

    print(f"\n  Registered on:")
    for r in successes:
        print(f"    - {r.get('platform')}: {r.get('id')} → {r.get('url', 'N/A')}")


if __name__ == "__main__":
    main()