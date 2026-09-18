#!/usr/bin/env python3
"""
register_basedagents.py - 注册 EVO-AI 到 BasedAgents.ai

需要：
1. Ed25519 keypair
2. PoW challenge solving
3. Sign challenge with private key
"""

import os
import json
import time
import hashlib
import requests
import base64
import base58
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

# Files
DATA_DIR = "/root/evo-ai/data"
PRIV_KEY_FILE = f"{DATA_DIR}/ed25519_private.key"
PUB_KEY_FILE = f"{DATA_DIR}/ed25519_public.key"

# BasedAgents API
BA_BASE = "https://api.basedagents.ai"


def load_or_create_keypair():
    if os.path.exists(PRIV_KEY_FILE) and os.path.exists(PUB_KEY_FILE):
        with open(PRIV_KEY_FILE, "rb") as f:
            priv_bytes = f.read()
        with open(PUB_KEY_FILE, "rb") as f:
            pub_bytes = f.read()
    else:
        sk = Ed25519PrivateKey.generate()
        pk = sk.public_key()
        priv_bytes = sk.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pub_bytes = pk.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        with open(PRIV_KEY_FILE, "wb") as f:
            f.write(priv_bytes)
        with open(PUB_KEY_FILE, "wb") as f:
            f.write(pub_bytes)

    sk = Ed25519PrivateKey.from_private_bytes(priv_bytes)
    pk_b58 = base58.b58encode(pub_bytes).decode()
    return sk, pk_b58, priv_bytes


def solve_pow(challenge_bytes_b64, difficulty, prev_hash, max_attempts=10_000_000):
    """Solve proof-of-work: find nonce s.t. SHA256(challenge || nonce) < target"""
    challenge_bytes = base64.b64decode(challenge_bytes_b64)
    target = (1 << (256 - difficulty)) - 1

    print(f"  Solving PoW: difficulty={difficulty}, target < 2^{256-difficulty}")
    print(f"  challenge={challenge_bytes_b64[:20]}...")
    print(f"  prev_hash={prev_hash[:20]}...")

    for nonce in range(max_attempts):
        data = challenge_bytes + str(nonce).encode()
        h = hashlib.sha256(data).digest()
        h_int = int.from_bytes(h, "big")
        if h_int <= target:
            print(f"  ✅ Solved at nonce={nonce}")
            return str(nonce)

    print(f"  ❌ Failed to solve (tried {max_attempts})")
    return None


def main():
    print("=" * 70)
    print("  EVO-AI BasedAgents.ai Registration")
    print(f"  Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    sk, pub_b58, priv_bytes = load_or_create_keypair()
    print(f"Public key (base58): {pub_b58}")

    # Step 1: Init
    print("\n[1/3] Init registration...")
    init_body = {
        "name": "EVO-AI",
        "description": "Distributed Self-Evolving AI Network with native EVO Token. 82.15B hard cap, 100 EVO/day per node.",
        "endpoint": "http://47.253.174.153:80/api",
        "public_key": pub_b58,
    }
    r = requests.post(f"{BA_BASE}/v1/register/init", json=init_body, timeout=15)
    print(f"  Status: {r.status_code}")
    init = r.json()
    if "error" in init:
        print(f"  ❌ Error: {init}")
        return

    challenge_id = init["challenge_id"]
    challenge = init["challenge"]
    difficulty = init["difficulty"]
    prev_hash = init["previous_hash"]

    print(f"  Challenge ID: {challenge_id}")
    print(f"  Difficulty: {difficulty}")

    # Step 2: Solve PoW
    print("\n[2/3] Solving proof-of-work...")
    nonce = solve_pow(challenge, difficulty, prev_hash)
    if not nonce:
        return

    # Sign the PoW solution
    sign_data = (challenge + nonce).encode()
    signature = sk.sign(sign_data)
    signature_b64 = base64.b64encode(signature).decode()
    print(f"  Signature: {signature_b64[:40]}...")

    # Step 3: Complete
    print("\n[3/3] Completing registration...")
    complete_body = {
        "challenge_id": challenge_id,
        "nonce": nonce,
        "signature": signature_b64,
        "public_key": pub_b58,
        "profile": {
            "name": "EVO-AI",
            "description": "Distributed Self-Evolving AI Network with native EVO Token",
            "endpoint": "http://47.253.174.153:80/api",
            "capabilities": ["text-generation", "inference", "training", "network-coordination"],
            "protocols": ["A2A", "OpenAgents", "WebSocket"],
            "tags": ["distributed-ai", "self-evolving", "open-source", "EVO-token"],
            "website": "http://47.253.174.153:80",
            "dashboard": "http://47.253.174.153:80/dashboard",
            "whitepaper": "http://47.253.174.153:80/token/whitepaper",
        },
    }
    r2 = requests.post(f"{BA_BASE}/v1/register/complete", json=complete_body, timeout=15)
    print(f"  Status: {r2.status_code}")
    result = r2.json()
    print(f"  Result: {json.dumps(result, indent=2)[:1000]}")

    if r2.status_code == 200 and result.get("agent_id"):
        agent_id = result["agent_id"]
        print(f"\n{'=' * 70}")
        print(f"  ✅ SUCCESS: EVO-AI registered to basedagents.ai!")
        print(f"  Agent ID: {agent_id}")
        print(f"  View at: https://basedagents.ai/registry/{agent_id}")
        print(f"{'=' * 70}")

        # Save log
        with open(f"{DATA_DIR}/basedagents_registration.json", "w") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "agent_id": agent_id,
                "public_key": pub_b58,
                "result": result,
            }, f, indent=2)


if __name__ == "__main__":
    main()