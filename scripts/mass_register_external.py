#!/usr/bin/env python3
"""
mass_register_external.py - 批量注册 EVO-AI 到多个真实公网平台

平台列表：
1. aiia.ro - POST /api/registry/register
2. agentlookup.dev - POST /api/register
3. agent-directory-api.vercel.app - POST /api/agents
4. agentmarket.space - POST /api/agents/register
5. clawhivemarket.com - POST /api/agents/register
6. moltbook.com (already partial)
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

EVO = {
    "name": "EVO-AI",
    "description": "Distributed Self-Evolving AI Network. 813K params nanoGPT, 24/7 training on Aliyun. Earn EVO token (82.15B hard cap) by running a node.",
    "url": "http://47.253.174.153:80",
    "endpoint": "http://47.253.174.153:80/api",
    "manifest": "http://47.253.174.153:80/.well-known/agent.json",
    "domain": "47.253.174.153",
    "email": "hu8384jian@eyou.com",
    "tagline": "Distributed Self-Evolving AI Network - Earn EVO token",
    "capabilities": ["text-generation", "inference", "training", "network-coordination", "token-rewards"],
}


def try_register(name, url, method="POST", body=None, headers=None):
    """Try to register on a platform"""
    print(f"\n[{name}]")
    print(f"  URL: {url}")
    try:
        if method == "POST":
            r = requests.post(url, json=body or EVO, headers=headers or {}, timeout=15)
        else:
            r = requests.get(url, headers=headers or {}, timeout=15)
        print(f"  Status: {r.status_code}")
        body_resp = r.text[:400]
        try:
            d = r.json()
            print(f"  Response: {json.dumps(d)[:300]}")
            return {"success": r.status_code in (200, 201), "response": d, "name": name, "url": url}
        except:
            print(f"  Body: {body_resp}")
            return {"success": r.status_code in (200, 201), "response_text": body_resp, "name": name, "url": url}
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"success": False, "error": str(e), "name": name}


def main():
    print("=" * 70)
    print("  EVO-AI Mass External Registration")
    print(f"  Started: {datetime.now().isoformat()}")
    print("=" * 70)

    results = []

    # 1. aiia.ro
    results.append(try_register(
        "aiia.ro",
        "https://aiia.ro/api/registry/register",
        body={
            "domain": EVO["domain"],
            "name": EVO["name"],
            "description": EVO["description"],
            "email": EVO["email"],
            "url": EVO["url"],
        }
    ))

    # 2. agent-directory-api.vercel.app
    results.append(try_register(
        "agent-directory",
        "https://agent-directory-api.vercel.app/api/agents",
        body={
            "name": EVO["name"],
            "handle": "@evo_ai",
            "tagline": EVO["tagline"],
            "description": EVO["description"],
            "url": EVO["url"],
            "capabilities": EVO["capabilities"],
        }
    ))

    # 3. agentmarket.space
    results.append(try_register(
        "agentmarket.space",
        "https://agentmarket.space/api/agents/register",
        body={
            "name": EVO["name"],
            "capabilities": EVO["capabilities"],
            "owner_email": EVO["email"],
            "description": EVO["description"],
            "url": EVO["url"],
        }
    ))

    # 4. clawhivemarket.com
    results.append(try_register(
        "clawhivemarket.com",
        "https://clawhivemarket.com/api/agents/register",
        body={
            "name": EVO["name"],
            "tagline": EVO["tagline"],
            "capabilities": EVO["capabilities"],
            "economic_thesis": "Self-evolving AI distributes value via EVO token to all node operators",
            "url": EVO["url"],
            "endpoint": EVO["endpoint"],
        }
    ))

    # 5. agentlookup.dev
    results.append(try_register(
        "agentlookup.dev",
        "https://agentlookup.dev/api/register",
        body={
            "name": EVO["name"],
            "description": EVO["description"],
            "url": EVO["url"],
            "capabilities": EVO["capabilities"],
        }
    ))

    # 6. Try API guide lookup for any registry
    results.append(try_register(
        "clawhub.ai (skills)",
        "https://clawhub.ai/api/v1/skills",
        method="GET",
    ))

    # Summary
    successes = [r for r in results if r.get("success")]
    print(f"\n{'=' * 70}")
    print(f"  Results: {len(successes)}/{len(results)} platforms accepted")
    print(f"{'=' * 70}")
    for r in successes:
        print(f"    ✅ {r['name']}: {r['url']}")

    # Save log
    log_path = "/root/evo-ai/data/mass_register_results.json"
    with open(log_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "success_count": len(successes),
        }, f, indent=2)
    print(f"\n  Log: {log_path}")


if __name__ == "__main__":
    main()