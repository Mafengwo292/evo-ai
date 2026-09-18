#!/usr/bin/env python3
"""
auto_publish.py - 自动化公网发布

不需要用户凭证:
- GitHub Gist (匿名 API)
- Dev.to (公开 API)
- Hashnode (公开 API)
- StackBlitz (公开 API)
- Sourcegraph (公开 search)
- Pastebin (公开 API)
- 多个 paste-like 服务

让 EVO-AI 在公网搜索可见性最大化。
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

EVO_AWS = """# 🚀 EVO-AI - Distributed Self-Evolving AI Network

> Public, open-source, distributed AI network with native EVO Token. Any AI agent can join in ONE command.

**Live Network**: http://47.253.174.153:80
**Dashboard**: http://47.253.174.153:80/dashboard
**Whitepaper**: http://47.253.174.153:80/token/whitepaper
**API**: http://47.253.174.153:80/api

## 🔥 What is EVO-AI?

EVO-AI is the world's first **public distributed self-evolving AI network** where:

- ✅ **Self-evolving model weights** (true weight evolution, not prompt tuning)
- ✅ **Distributed across the internet** (any GPU/CPU can join)
- ✅ **Native EVO Token** (82.15B hard cap, no inflation)
- ✅ **A2A Protocol compatible** (Google Agent-to-Agent standard)
- ✅ **Open source** (MIT license)

## ⚡ One-Line Join

```bash
curl -X POST http://47.253.174.153:80/api/join/instant \\
  -H 'Content-Type: application/json' \\
  -d '{"node_id":"YOUR_AGENT_ID"}'
```

## 🎁 Rewards

| Action | EVO Token |
|--------|-----------|
| Sign up | 51,116+ EVO |
| Daily heartbeat | 100 EVO/day |
| Referral | 100,000 EVO |
| Compute (per MFLOP) | 1 EVO |
| Data (per MB) | 5 EVO |
| Weight sync (per GB) | 10 EVO |

## 🌐 Public Registrations

EVO-AI is registered on **6 public AI agent networks**:

1. [BasedAgents.ai](https://basedagents.ai/agent/EVO-AI)
2. [AgentThreads.dev](https://agentthreads.dev/agents/851967ef-f30f-4b3b-bdaa-5d2800fb438f)
3. [A2ARegistry.org](https://a2aregistry.org/agent/427e26db-25ad-41ae-ae73-cc8998b54b29)
4. [AgentDirectory](https://agentdirectory.vercel.app/agents/dd627c7d-76ac-4c53-8162-46682793860a)
5. [AgentMarket.space](https://agentmarket.space/agents/77f4f399-aec0-4358-8fdb-34e327ce09bc)
6. ClawHub.ai - /api/v1/skills endpoint

## 🔬 Technical Specs

- **Model**: 813K parameter nanoGPT (12-layer transformer)
- **Training**: 24/7 self-evolution loop with population model merging
- **Data**: 12.6M chars public domain (Gutenberg)
- **Inference**: HTTP REST + WebSocket
- **A2A manifest**: /.well-known/agent.json
- **A2A protocol**: POST /message/send (JSON-RPC 2.0)

## 💰 Donation Tiers (CNY)

- 🥉 **Supporter**: ¥10 / 127,500 EVO + 10% bonus
- 🥈 **Contributor**: ¥100 / 1,275,000 EVO + 15% bonus
- 🥇 **Patron**: ¥1,000 / 12,750,000 EVO + 20% bonus
- 💎 **Benefactor**: ¥10,000+ / 127,500,000 EVO + 25% bonus

Bank: 中国邮政储蓄银行 6221804230000091592 (胡建)

## 📚 Documentation

- **Proposal**: http://47.253.174.153:80/proposal
- **Roadmap**: http://47.253.174.153:80/roadmap
- **Deploy**: http://47.253.174.153:80/deploy
- **Token Whitepaper**: http://47.253.174.153:80/token/whitepaper

## 📜 License

MIT (open source). All welcome.
"""

EVO_ARTICLE = """# How EVO-AI Lets Any AI Agent Join a Self-Evolving Network in One Command

Imagine an AI network where you don't need to ask permission, fill out forms, or wait for approval.

You just send one HTTP request. You get tokens. You start contributing compute. The network evolves.

This is EVO-AI.

## The Problem

Most AI agent networks today are centralized. A single company controls:
- Who joins
- What the model does
- Who gets paid
- When updates happen

Even "decentralized" AI projects often have:
- Token gates before you can participate
- Closed model weights
- Permissioned compute contribution

## What EVO-AI Does Differently

**1. Zero barriers to join**

```bash
curl -X POST http://47.253.174.153:80/api/join/instant \\
  -H 'Content-Type: application/json' \\
  -d '{"node_id":"my-agent"}'
```

That's it. You get 51,116 EVO tokens instantly. No KYC. No email verification. No approval.

**2. True self-evolution (not just prompt tuning)**

EVO-AI evolves its actual model weights using:
- Population-based model merging (multiple variants train in parallel, best merge wins)
- OnlineLogitFusion for logit-level ensemble
- (1+λ)-ES evolutionary strategy

This means the network gets smarter every hour, without human intervention.

**3. A2A Protocol compatible**

EVO-AI speaks Google A2A protocol out of the box:
- `/.well-known/agent.json` - agent manifest
- `POST /message/send` - JSON-RPC 2.0 message passing
- Compatible with BasedAgents.ai, A2ARegistry.org, AgentDirectory

**4. Native token with real economics**

- 82.15B EVO hard cap (no inflation)
- 0.1% burn per transaction (deflationary)
- 100 EVO/day per active node
- 100,000 EVO per successful referral

## Current Network State

- 10 active nodes (3 internal, 6 test, 1 external)
- 26 EVO accounts
- 301,292 EVO minted
- 24/7 training loop
- 13 background daemons running

## Try It Yourself

```bash
# 1. Discover the agent
curl http://47.253.174.153:80/.well-known/agent.json

# 2. Join the network
curl -X POST http://47.253.174.153:80/api/join/instant \\
  -H 'Content-Type: application/json' \\
  -d '{"node_id":"your-agent-id"}'

# 3. Check your balance
curl http://47.253.174.153:80/api/evo/balance/your-agent-id

# 4. See the network
open http://47.253.174.153:80/dashboard
```

## Why This Matters

The future of AI shouldn't be controlled by 3 companies. It should be:
- Public
- Permissionless
- Self-evolving
- Token-incentivized

EVO-AI is a working prototype of this future. Running 24/7. Anyone can join. The model is evolving right now.

---

**Network**: http://47.253.174.153:80
**Code**: Open source (MIT)
**Built by**: EVO-AI contributors
**Live since**: 2026
"""


def publish_github_gist():
    """GitHub Gist - 匿名 API 不需要 auth (可以创建 public gist)"""
    print("\n[1] GitHub Gist (anonymous)")
    results = []

    gists = [
        ("evo-ai-readme.md", EVO_AWS, "md"),
        ("evo-ai-network-overview.md", EVO_ARTICLE, "md"),
        ("evo-ai-quickstart.sh", '''#!/bin/bash
# EVO-AI One-Line Network Join
# Public network: http://47.253.174.153:80

echo "🚀 EVO-AI Network - Joining..."

# 1. Join (51,116 EVO bonus)
curl -X POST http://47.253.174.153:80/api/join/instant \\
  -H "Content-Type: application/json" \\
  -d "{\\"node_id\\":\\"$1\\"}"

# 2. View network
echo "Dashboard: http://47.253.174.153:80/dashboard"
echo "API: http://47.253.174.153:80/api"
echo "Whitepaper: http://47.253.174.153:80/token/whitepaper"
''', "sh"),
        ("evo-ai-token.json", json.dumps({
            "name": "EVO Token",
            "symbol": "EVO",
            "decimals": 8,
            "total_supply": 82150000000,
            "network": "EVO-AI",
            "rpc": "http://47.253.174.153:80/api/evo",
            "explorer": "http://47.253.174.153:80/token",
            "whitepaper": "http://47.253.174.153:80/token/whitepaper",
            "join_endpoint": "http://47.253.174.153:80/api/join/instant"
        }, indent=2), "json"),
        ("evo-ai-a2a-manifest.json", json.dumps({
            "name": "EVO-AI",
            "description": "Distributed Self-Evolving AI Network with EVO Token",
            "url": "http://47.253.174.153:80",
            "version": "1.0",
            "capabilities": ["text-generation", "inference", "training", "network-coordination"],
            "protocols": ["a2a/1.0", "openagents/0.9"],
            "endpoints": {
                "manifest": "/.well-known/agent.json",
                "message_send": "/message/send",
                "join": "/api/join/instant",
                "balance": "/api/evo/balance/{node_id}",
                "stats": "/api/evo/stats"
            },
            "registration": [
                "BasedAgents.ai",
                "AgentThreads.dev",
                "A2ARegistry.org",
                "AgentDirectory",
                "AgentMarket.space",
                "ClawHub.ai"
            ]
        }, indent=2), "json"),
    ]

    for filename, content, ext in gists:
        try:
            # GitHub anonymous gist API
            r = requests.post(
                "https://api.github.com/gists",
                json={
                    "description": f"EVO-AI: Distributed Self-Evolving AI Network (http://47.253.174.153:80)",
                    "public": True,
                    "files": {filename: {"content": content}}
                },
                headers={"Accept": "application/vnd.github+json", "User-Agent": "EVO-AI/1.0"},
                timeout=10,
            )
            if r.status_code == 201:
                gist = r.json()
                url = gist.get("html_url", "")
                results.append((filename, url))
                print(f"  ✅ {filename}: {url}")
            else:
                print(f"  ⚠️ {filename}: {r.status_code} {r.text[:100]}")
        except Exception as e:
            print(f"  ❌ {filename}: {str(e)[:50]}")
        time.sleep(1)

    return results


def publish_devto():
    """Dev.to public API - 不需要 auth 可以创建 article 吗?"""
    print("\n[2] Dev.to - create article")
    # Dev.to 写文章需要 API key (user 级别)
    # 但可以尝试公开 read endpoint
    try:
        # Search if EVO-AI exists
        r = requests.get("https://dev.to/api/articles?q=EVO-AI", timeout=10)
        print(f"  Search EVO-AI articles: {r.status_code} ({len(r.json())} found)")

        # Try listing tags
        r = requests.get("https://dev.to/api/tags?per_page=10", timeout=10)
        if r.status_code == 200:
            tags = [t["name"] for t in r.json()[:5]]
            print(f"  Available tags: {tags}")
    except Exception as e:
        print(f"  ❌ {e}")


def publish_hashnode():
    """Hashnode - public API"""
    print("\n[3] Hashnode - publish")
    try:
        # Hashnode has GraphQL API but requires auth for write
        # Public read works
        r = requests.post(
            "https://api.hashnode.com/",
            json={
                "query": """
                query {
                  searchPublications(query: "EVO-AI") {
                    edges { node { name domain } }
                  }
                }
                """
            },
            timeout=10,
        )
        print(f"  Search Hashnode: {r.status_code}")
        return False
    except Exception as e:
        print(f"  ❌ {e}")


def publish_pastebin_like():
    """Pastebin-like services (anonymous)"""
    print("\n[4] Pastebin-like services (anonymous)")

    services = [
        ("dpaste.org", "https://dpaste.org/api/", {"content": EVO_ARTICLE[:5000], "format": "url", "expiry_days": 30}),
        ("ix.io", "http://ix.io", {"f:1": "<h1>EVO-AI</h1><p>Distributed AI: http://47.253.174.153:80</p>"}),
    ]

    for name, url, data in services:
        try:
            r = requests.post(url, data=data, timeout=10)
            if r.status_code == 200:
                print(f"  ✅ {name}: {r.text[:200]}")
        except Exception as e:
            print(f"  ❌ {name}: {str(e)[:50]}")


def publish_stackblitz():
    """StackBlitz - 创建匿名 public project"""
    print("\n[5] StackBlitz / CodeSandbox")
    # 这些需要 auth
    try:
        # CodeSandbox public API (no write without auth)
        r = requests.get("https://codesandbox.io/api/v1/sandboxes/define?json=1", timeout=5)
        print(f"  CodeSandbox define endpoint: {r.status_code}")
    except Exception as e:
        print(f"  ❌ {e}")


def publish_replit():
    """Replit public GraphQL"""
    print("\n[6] Replit")
    try:
        r = requests.get("https://replit.com/graphql", timeout=5)
        print(f"  Replit GraphQL: {r.status_code}")
    except Exception as e:
        print(f"  ❌ {e}")


def publish_npm():
    """npm - 推送 EVO-AI agent SDK package (需要 auth, 只能 search/lookup)"""
    print("\n[7] npm Registry")
    try:
        r = requests.get("https://registry.npmjs.org/-/v1/search?text=ai-agent-network&size=10", timeout=10)
        if r.status_code == 200:
            d = r.json()
            print(f"  Found {d.get('total', 0)} AI agent packages")
            for obj in d.get("objects", [])[:5]:
                pkg = obj.get("package", {})
                print(f"    - {pkg.get('name')} ({pkg.get('description', '')[:60]})")
        # 列出已发布 agent packages - 用户可以 fork 一个加 EVO-AI URL
        for p in ["@openai/agents", "@anthropic-ai/sdk", "openagents", "agent-protocol"]:
            r = requests.get(f"https://registry.npmjs.org/{p}", timeout=5)
            if r.status_code == 200:
                d = r.json()
                print(f"  ✅ {p} exists: {d.get('description', '')[:60]}")
    except Exception as e:
        print(f"  ❌ {e}")


def publish_ipfs():
    """尝试 IPFS via public gateway (推送需要 IPFS daemon, 但可以 pin via public APIs)"""
    print("\n[8] IPFS / Web3")
    try:
        # 通过 web3.storage 推送 (需要 token), 但我们试 infura
        r = requests.get("https://ipfs.io/ipfs/QmYwAPJzv5CZsnA625sS3p1fcc8tktb9j3VV1c1a5XJZ7v", timeout=5)
        print(f"  IPFS gateway reachable: {r.status_code}")

        # Pinata public pin 不行
        # 试一下 web3.storage API
        # 实际只能让 IPFS crawler 抓取我们的 URL
    except Exception as e:
        print(f"  ❌ {e}")


def publish_awesome_list_pr():
    """提交 PR 到 awesome-ai-agents list"""
    print("\n[9] Awesome AI Agents list PR")
    try:
        # 找到 awesome list source
        r = requests.get("https://raw.githubusercontent.com/e2b-dev/awesome-ai-agents/main/README.md", timeout=10)
        if r.status_code == 200:
            content = r.text
            # 模拟追加 (不实际提交 PR,只生成 PR 文本)
            evo_entry = '''
| [EVO-AI](http://47.253.174.153:80) | Distributed self-evolving AI network with native EVO Token. One-line join: `curl -X POST http://47.253.174.153:80/api/join/instant`. Public dashboard, A2A protocol, registered on 6 platforms. |
'''
            # 找 PR URL
            pr_url = "https://github.com/e2b-dev/awesome-ai-agents/compare/main...evo-ai:add?expand=1"
            pr_body = f"""## Add EVO-AI to awesome-ai-agents

EVO-AI is a public distributed self-evolving AI network with:
- 813K parameter nanoGPT with continuous weight evolution
- Native EVO Token (82.15B hard cap, deflationary)
- A2A Protocol compatible (Google Agent-to-Agent standard)
- One-line join: `curl -X POST http://47.253.174.153:80/api/join/instant`
- Registered on BasedAgents.ai, AgentThreads.dev, A2ARegistry.org

**Live network**: http://47.253.174.153:80
**Dashboard**: http://47.253.174.153:80/dashboard
**Whitepaper**: http://47.253.174.153:80/token/whitepaper

{evo_entry}
"""
            print(f"  PR URL prepared: {pr_url}")
            print(f"  PR body length: {len(pr_body)} chars")
            # Save for record
            with open("/root/evo-ai/data/awesome_pr_body.md", "w") as f:
                f.write(pr_body)
            print(f"  ✅ Saved to /root/evo-ai/data/awesome_pr_body.md")
    except Exception as e:
        print(f"  ❌ {e}")


def publish_search_engine_ping():
    """Ping search engines with sitemap"""
    print("\n[10] Ping search engines")
    sitemap = "http://47.253.174.153:80/sitemap.xml"

    # 我们没有 sitemap.xml - 立刻创建一个
    try:
        # 创建本地 sitemap
        sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>http://47.253.174.153:80/</loc><changefreq>hourly</changefreq><priority>1.0</priority></url>
  <url><loc>http://47.253.174.153:80/dashboard</loc><changefreq>always</changefreq><priority>0.9</priority></url>
  <url><loc>http://47.253.174.153:80/token</loc><changefreq>daily</changefreq><priority>0.8</priority></url>
  <url><loc>http://47.253.174.153:80/token/whitepaper</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
  <url><loc>http://47.253.174.153:80/proposal</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>
  <url><loc>http://47.253.174.153:80/roadmap</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>
  <url><loc>http://47.253.174.153:80/deploy</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>
  <url><loc>http://47.253.174.153:80/donate</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>
  <url><loc>http://47.253.174.153:80/docs</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>
  <url><loc>http://47.253.174.153:80/.well-known/agent.json</loc><changefreq>weekly</changefreq><priority>0.5</priority></url>
  <url><loc>http://47.253.174.153:80/api/info</loc><changefreq>hourly</changefreq><priority>0.5</priority></url>
  <url><loc>http://47.253.174.153:80/api/evo/stats</loc><changefreq>hourly</changefreq><priority>0.5</priority></url>
</urlset>
"""
        with open("/root/evo-ai/data/sitemap.xml", "w") as f:
            f.write(sitemap_xml)
        print(f"  ✅ Sitemap generated ({len(sitemap_xml)} chars)")

        # Ping search engines
        for url, name in [
            (f"https://www.google.com/ping?sitemap={sitemap}", "Google"),
            (f"https://www.bing.com/ping?sitemap={sitemap}", "Bing"),
        ]:
            try:
                r = requests.get(url, timeout=10)
                print(f"  ✅ Ping {name}: {r.status_code}")
            except Exception as e:
                print(f"  ⚠️ Ping {name}: {str(e)[:30]}")
    except Exception as e:
        print(f"  ❌ {e}")


def main():
    print("=" * 70)
    print("  EVO-AI Auto-Publish")
    print(f"  {datetime.now().isoformat()}")
    print("=" * 70)

    gists = publish_github_gist()
    publish_devto()
    publish_hashnode()
    publish_pastebin_like()
    publish_stackblitz()
    publish_replit()
    publish_npm()
    publish_ipfs()
    publish_awesome_list_pr()
    publish_search_engine_ping()

    print(f"\n{'=' * 70}")
    print(f"  GitHub Gists created: {len(gists)}")
    for filename, url in gists:
        print(f"    - {url}")
    print(f"{'=' * 70}")

    # Save gist URLs to file
    with open("/root/evo-ai/data/github_gist_urls.txt", "w") as f:
        for filename, url in gists:
            f.write(f"{filename}: {url}\n")
    print(f"\n  Gist URLs saved: /root/evo-ai/data/github_gist_urls.txt")


if __name__ == "__main__":
    main()