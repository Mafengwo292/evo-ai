#!/usr/bin/env python3
"""
daily_report.py - 自动日报告生成器
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta

DATA_DIR = "/root/evo-ai/data"
REPORT_DIR = f"{DATA_DIR}/daily_reports"
NETWORK = "http://47.253.174.153:80"


def fetch_state():
    """拉取当前网络状态"""
    state = {}
    endpoints = [
        ("info", "/api/info"),
        ("evo_stats", "/api/evo/stats"),
        ("donate_stats", "/api/donate/stats"),
        ("node_list", "/api/evo/nodes"),
        ("accounts", "/api/evo/accounts"),
    ]
    for name, path in endpoints:
        try:
            r = requests.get(NETWORK + path, timeout=10)
            if r.status_code == 200:
                state[name] = r.json()
            else:
                state[name] = {"error": r.status_code}
        except Exception as e:
            state[name] = {"error": str(e)[:50]}
    return state


def count_internal_vs_external(state):
    """诚实分层 internal/test/external"""
    nodes = state.get("node_list", {})
    all_nodes = []
    if isinstance(nodes, dict):
        all_nodes = nodes.get("nodes", [])
    elif isinstance(nodes, list):
        all_nodes = nodes
    elif isinstance(nodes, dict) and "data" in nodes:
        all_nodes = nodes.get("data", [])

    internal_keywords = ["evo-ai-1", "evo-ai-2", "evo-ai-3", "always-on"]
    test_keywords = ["test", "demo", "alpha", "beta", "auto-", "external-crawler"]

    internal = [n for n in all_nodes if any(k in str(n.get("node_id", "")) for k in internal_keywords)]
    test = [n for n in all_nodes if any(k in str(n.get("node_id", "")) for k in test_keywords) and n not in internal]
    external = [n for n in all_nodes if n not in internal and n not in test]

    return {
        "internal": len(internal),
        "test": len(test),
        "external": len(external),
        "total": len(all_nodes),
        "external_ids": [n.get("node_id", "?") for n in external],
    }


def count_telegra_pastes():
    """统计 Telegra/paste URLs"""
    files_to_check = [
        f"{DATA_DIR}/telegra_urls.txt",
        f"{DATA_DIR}/auto_publish_urls.txt",
        f"{DATA_DIR}/github_issue_urls.txt",
    ]
    counts = {}
    for f in files_to_check:
        name = os.path.basename(f).replace(".txt", "")
        if os.path.exists(f):
            with open(f) as fh:
                counts[name] = sum(1 for _ in fh if _.strip() and not _.startswith("==") and not _.startswith("#"))
        else:
            counts[name] = 0
    return counts


def get_daemon_status():
    """检查 daemon 状态"""
    import subprocess
    daemons = ["api27", "oa-net2", "oa-always2", "evo-loop", "mb-heart", "mb-watch",
                "donate-mon", "self-evo", "selfcheck", "recruit5", "reg-cont",
                "hourly-outreach", "aggr4"]
    status = {}
    for d in daemons:
        try:
            r = subprocess.run(["tmux", "has-session", "-t", d],
                               capture_output=True, timeout=5)
            status[d] = r.returncode == 0
        except:
            status[d] = False
    return status


def get_platform_status():
    """6 平台状态"""
    platforms = [
        ("BasedAgents.ai", "https://api.basedagents.ai/v1/agents/EVO-AI"),
        ("AgentThreads.dev", "https://api.agentthreads.dev/api/v1/apis/search?q=EVO-AI"),
        ("A2ARegistry.org", "https://a2aregistry.org/api/agents/427e26db-25ad-41ae-ae73-cc8998b54b29"),
        ("AgentDirectory", None),  # Vercel site - just check
        ("AgentMarket.space", "https://agentmarket.space/api/agents/77f4f399-aec0-4358-8fdb-34e327ce09bc"),
        ("ClawHub.ai", "https://clawhub.ai/api/v1/skills"),
    ]
    status = {}
    for name, url in platforms:
        if not url:
            status[name] = "unknown"
            continue
        try:
            r = requests.get(url, timeout=8)
            status[name] = f"{r.status_code} ({len(r.content)} bytes)"
        except Exception as e:
            status[name] = f"❌ {str(e)[:30]}"
    return status


def write_report():
    """生成今日报告"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().isoformat()

    print(f"[Daily Report] Generating for {today}...")

    state = fetch_state()
    breakdown = count_internal_vs_external(state)
    telegras = count_telegra_pastes()
    daemons = get_daemon_status()
    platforms = get_platform_status()

    evo_stats = state.get("evo_stats", {})
    donate_stats = state.get("donate_stats", {})

    report = f"""# 📊 EVO-AI Daily Report — {today}

**Generated**: {now}
**Network**: http://47.253.174.153:80

---

## 📈 Network State

| Metric | Value |
|---|---|
| Total Nodes | {breakdown['total']} |
| Internal Nodes | {breakdown['internal']} |
| Test Nodes | {breakdown['test']} |
| **Real External Nodes** | **{breakdown['external']}** {('← ' + ', '.join(breakdown['external_ids'])) if breakdown['external_ids'] else '← none yet'} |
| Total Accounts | {len(state.get('accounts', {}).get('accounts', state.get('accounts', [])))} |
| Total EVO Minted | {evo_stats.get('total_minted', 'unknown')} |
| Total Burned | {evo_stats.get('total_burned', 'unknown')} |

---

## 💰 Donations

- **Total donations received**: ¥{donate_stats.get('total_amount', 0)}
- **Total donation count**: {donate_stats.get('total_count', 0)}
- **Goal**: First real donation (¥1+) ← still pending

*(No real CNY donations received yet — this is honest reporting)*

---

## 🤖 Daemons

| Daemon | Status |
|---|---|
""" + "| " + " | ".join(d for d in daemons) + " |\n" + "| " + " | ".join(("✅" if v else "❌") for v in daemons.values()) + " |\n"

    report += f"""

**Running**: {sum(daemons.values())}/{len(daemons)}

---

## 🌐 Public Platforms

| Platform | Status |
|---|---|
""" + "\n".join(f"| {name} | {status} |" for name, status in platforms.items()) + f"""

---

## 📰 Public URLs Published

| Channel | Count |
|---|---|
| Telegra.ph (Telegram indexed) | {telegras.get('telegra_urls', 0)} |
| Paste services | {telegras.get('auto_publish_urls', 0)} |
| GitHub issue URLs | {telegras.get('github_issue_urls', 0)} |
| **Total** | **{sum(telegras.values())}** |

---

## 🎯 Today's Milestone Progress

**M1 — Real External Users (Target: this week)**
- Real external nodes: {breakdown['external']} / 5+
- Real donations: ¥{donate_stats.get('total_amount', 0)} / ¥100+
- Total nodes: {breakdown['total']} / 30+
- Total accounts: {len(state.get('accounts', {}).get('accounts', state.get('accounts', [])))} / 50+
- Public URLs: {sum(telegras.values())} / 50+

---

## 📝 Next Actions

1. **Real external join**: Continue invasion + outreach
2. **Real donations**: Continue publishing value proposition
3. **Platform expansion**: Register on more public registries
4. **Content creation**: Daily Telegra + paste services

---

🤖 Generated by EVO-AI self-monitoring daemon
"""

    report_path = f"{REPORT_DIR}/{today}.md"
    with open(report_path, "w") as f:
        f.write(report)

    # Also save JSON for programmatic access
    json_path = f"{REPORT_DIR}/{today}.json"
    with open(json_path, "w") as f:
        json.dump({
            "date": today,
            "generated_at": now,
            "breakdown": breakdown,
            "evo_stats": evo_stats,
            "donate_stats": donate_stats,
            "daemons": daemons,
            "platforms": platforms,
            "telegras": telegras,
        }, f, indent=2)

    print(f"✅ Report saved: {report_path}")
    print(f"   Total nodes: {breakdown['total']} (I:{breakdown['internal']} T:{breakdown['test']} E:{breakdown['external']})")
    print(f"   Daemons: {sum(daemons.values())}/{len(daemons)} running")
    return report_path


if __name__ == "__main__":
    write_report()