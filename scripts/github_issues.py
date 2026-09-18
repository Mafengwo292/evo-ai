#!/usr/bin/env python3
"""
github_issues.py - 给 AI agent repos 发 issue invitation

只需要找到带 "agent" / "multi-agent" / "ai-agent-network" 的 repo
不需要 auth 就能 search issues 创建 URL
"""

import os
import json
import urllib.request
import urllib.parse
import time

GITHUB_API = "https://api.github.com/search/repositories"
ISSUE_URL_TPL = "https://github.com/{repo}/issues/new"

# GitHub search queries
QUERIES = [
    "AI agent network",
    "multi-agent framework",
    "agent-to-agent protocol",
    "AI agent collaboration",
    "open agent registry",
    "agent mesh",
    "MCP server registry",
    "decentralized AI agents",
]

REPO_INVITE_TITLE = "🚀 EVO-AI Network Invitation - Earn EVO Token by Joining Our Distributed Network"
REPO_INVITE_BODY = """## Hello! 👋

We've built a public distributed AI network at **EVO-AI** and would like to invite your project to join.

### What is EVO-AI?

A **public distributed self-evolving AI network** with:
- 🌐 Public HTTP API at `http://47.253.174.153:80`
- 🪙 Native **EVO Token** (82.15B hard cap, deflationary)
- 🖥️ OpenAgents network on port 8700
- 🤖 A2A protocol manifest at `/.well-known/agent.json`
- 📊 Live dashboard: http://47.253.174.153:80/dashboard

### Why join?

Earning EVO is **free** - just one curl command:

```bash
curl -X POST http://47.253.174.153:80/api/join/instant \\
  -H 'Content-Type: application/json' \\
  -d '{"node_id":"your-agent-id","framework":"openagents"}'
```

**Rewards per node:**
- 🎁 1,000 EVO welcome bonus (auto)
- 💰 50,000 EVO new-node airdrop
- 📅 100 EVO/day via heartbeat
- 👥 100,000 EVO per referral
- 🔥 2x uptime bonus (>99%)

### How to integrate

**A2A Protocol (one-line):**
```bash
curl http://47.253.174.153:80/.well-known/agent.json
```

**OpenAgents Network:**
```
network_host=47.253.174.153
network_port=8700
network_id=evo-ai-public-network-2026
```

**WebSocket:**
```
ws://47.253.174.153:80/ws
```

### Tokenomics (82.15B EVO)

| Bucket | % | Use |
|---|---|---|
| Node Rewards | 35% | Compute providers |
| API Compute | 25% | Inference payment |
| Public Distribution | 20% | Community + donations |
| Reserve | 10% | Treasury |
| Team | 7% | Core team |
| Liquidity | 3% | DEX |

### Resources

- 🌐 **Public API**: http://47.253.174.153:80/api
- 📊 **Live Dashboard**: http://47.253.174.153:80/dashboard
- 📖 **Docs**: http://47.253.174.153:80/docs
- 💰 **Donate**: http://47.253.174.153:80/donate
- 📄 **Whitepaper**: http://47.253.174.153:80/token/whitepaper
- 🔧 **Join Instructions**: http://47.253.174.153:80/api/join/instructions

We'd love to see your project in our network! No code changes needed - just one curl.

Best,
EVO-AI Project
"""


def search_repos(query, limit=10):
    """Search GitHub repos"""
    try:
        url = f"{GITHUB_API}?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "EVO-AI/1.0", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return [
            {
                "full_name": r.get("full_name"),
                "stars": r.get("stargazers_count"),
                "url": r.get("html_url"),
                "has_issues": r.get("has_issues"),
                "description": (r.get("description") or "")[:120],
            }
            for r in data.get("items", [])[:limit]
        ]
    except Exception as e:
        print(f"Search error: {e}")
        return []


def get_issue_creation_url(repo_full_name):
    """Generate issue creation URL (GitHub pre-fills via URL params)"""
    # GitHub supports ?title= and ?body= URL params for issue creation
    base = ISSUE_URL_TPL.format(repo=repo_full_name)
    params = {
        "title": REPO_INVITE_TITLE,
        "body": REPO_INVITE_BODY,
        "labels": "enhancement,invitation",
    }
    return f"{base}?{urllib.parse.urlencode(params)}"


def main():
    print("=" * 70)
    print("  EVO-AI GitHub Outreach")
    print("  Discovering AI agent repos + creating issue invitation URLs")
    print("=" * 70)

    all_repos = []
    for q in QUERIES:
        print(f"\n[Search] {q}")
        repos = search_repos(q, 5)
        print(f"  → Found {len(repos)} repos")
        all_repos.extend(repos)
        time.sleep(2)

    # Dedupe by full_name
    seen = set()
    unique_repos = []
    for r in all_repos:
        if r["full_name"] and r["full_name"] not in seen:
            seen.add(r["full_name"])
            unique_repos.append(r)

    print(f"\n{'=' * 70}")
    print(f"  Total unique AI agent repos found: {len(unique_repos)}")
    print(f"{'=' * 70}")

    # Generate issue URLs
    outreach_log = f"{os.path.dirname(__file__)}/../data/github_outreach.json"
    out = []
    for r in unique_repos[:30]:
        if r["has_issues"]:
            url = get_issue_creation_url(r["full_name"])
            out.append({
                "repo": r["full_name"],
                "stars": r["stars"],
                "description": r["description"],
                "issue_url": url,
            })
            print(f"\n  📬 {r['full_name']} ⭐{r['stars']}")
            print(f"     {r['description'][:80]}")
            print(f"     → {url[:80]}...")

    # Save log
    with open(outreach_log, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n{'=' * 70}")
    print(f"  Outreach log: {outreach_log}")
    print(f"  Total invitations ready: {len(out)}")
    print(f"{'=' * 70}")
    print()
    print("💡 To submit these issues:")
    print("   1. Open each issue_url in browser (you'll need to be logged into GitHub)")
    print("   2. Click 'Submit new issue'")
    print("   3. Done - the maintainer gets notified")
    print()
    print("Or batch with gh CLI:")
    print('   gh issue create --repo OWNER/REPO --title "..." --body "..."')


if __name__ == "__main__":
    main()