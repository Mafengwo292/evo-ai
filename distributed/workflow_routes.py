#!/usr/bin/env python3
"""
workflow_routes.py - 公网工作流 + 里程碑路由
"""

import os
import json
import time
import subprocess
import requests
from datetime import datetime, timedelta

DATA_DIR = "/root/evo-ai/data"
WORKFLOW_MD = "/root/evo-ai/WORKFLOW_24H.md"
MILESTONES_MD = "/root/evo-ai/MILESTONES.md"


def render_workflow_page():
    """渲染 workflow markdown → HTML"""
    if not os.path.exists(WORKFLOW_MD):
        return "<h1>Workflow doc missing</h1>", 404

    with open(WORKFLOW_MD) as f:
        md = f.read()

    # Simple markdown → HTML
    html = []
    for line in md.split("\n"):
        if line.startswith("# "):
            html.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            html.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            html.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("|") and "|" in line[1:]:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            html.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
        elif line.startswith("- "):
            html.append(f"<li>{line[2:]}</li>")
        elif line.startswith("```"):
            html.append("<pre>")
        elif line.strip():
            if "<pre>" in "".join(html[-1:]):
                html.append(line)
            else:
                html.append(f"<p>{line}</p>")

    body = "".join(html)

    return f"""<!DOCTYPE html>
<html>
<head>
  <title>EVO-AI Workflow</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="30">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #0a0e1a; color: #c5cdd9; }}
    h1, h2, h3 {{ color: #00ff88; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
    td, th {{ border: 1px solid #2a3142; padding: 8px; text-align: left; }}
    td {{ background: #11151f; }}
    pre {{ background: #11151f; padding: 12px; border-radius: 6px; overflow-x: auto; }}
    a {{ color: #00ddff; }}
    code {{ background: #1a1f2e; padding: 2px 6px; border-radius: 3px; color: #00ff88; }}
  </style>
</head>
<body>
  {body}
  <hr/>
  <p><a href="/dashboard">📊 Dashboard</a> | <a href="/live">🟢 Live</a> | <a href="/token">💎 Token</a> | <a href="/proposal">📜 Proposal</a></p>
</body>
</html>
""", 200


def render_milestones_page():
    if not os.path.exists(MILESTONES_MD):
        return "<h1>Milestones doc missing</h1>", 404

    with open(MILESTONES_MD) as f:
        md = f.read()

    html = []
    for line in md.split("\n"):
        if line.startswith("# "):
            html.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            html.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            html.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("|") and "|" in line[1:]:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            html.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
        elif line.startswith("- "):
            html.append(f"<li>{line[2:]}</li>")
        elif line.strip():
            html.append(f"<p>{line}</p>")

    body = "".join(html)
    return f"""<!DOCTYPE html>
<html>
<head>
  <title>EVO-AI Milestones</title>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="30">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #0a0e1a; color: #c5cdd9; }}
    h1, h2, h3 {{ color: #00ff88; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
    td, th {{ border: 1px solid #2a3142; padding: 8px; }}
    td {{ background: #11151f; }}
    a {{ color: #00ddff; }}
  </style>
</head>
<body>
  {body}
  <p><a href="/dashboard">📊 Dashboard</a> | <a href="/workflow">⚙️ Workflow</a></p>
</body>
</html>
""", 200


def render_status_json():
    """实时 status JSON"""
    NETWORK = "http://47.253.174.153:80"

    status = {"timestamp": datetime.now().isoformat()}

    # Nodes + accounts + EVO
    try:
        r = requests.get(f"{NETWORK}/api/evo/nodes", timeout=5)
        if r.status_code == 200:
            d = r.json()
            nodes = d.get("nodes", [])
            if isinstance(nodes, dict):
                nodes = list(nodes.values())
            status["nodes"] = nodes
            status["nodes_count"] = len(nodes)
    except:
        status["nodes_count"] = None

    try:
        r = requests.get(f"{NETWORK}/api/evo/accounts", timeout=5)
        if r.status_code == 200:
            d = r.json()
            accs = d.get("accounts", [])
            if isinstance(accs, dict):
                accs = list(accs.values())
            status["accounts"] = accs
            status["accounts_count"] = len(accs)
    except:
        status["accounts_count"] = None

    try:
        r = requests.get(f"{NETWORK}/api/evo/stats", timeout=5)
        if r.status_code == 200:
            status["evo_stats"] = r.json()
    except:
        pass

    try:
        r = requests.get(f"{NETWORK}/api/donate/stats", timeout=5)
        if r.status_code == 200:
            status["donate_stats"] = r.json()
    except:
        pass

    # Daemons
    daemons = ["api27", "oa-net2", "oa-always2", "evo-loop", "mb-heart",
                "self-evo", "selfcheck", "recruit5", "reg-cont", "hourly-outreach",
                "donate-mon"]
    status["daemons"] = {}
    for d in daemons:
        try:
            r = subprocess.run(["tmux", "has-session", "-t", d],
                               capture_output=True, timeout=5)
            status["daemons"][d] = r.returncode == 0
        except:
            status["daemons"][d] = False

    # Cron
    try:
        r = subprocess.run(["crontab", "-l"], capture_output=True, timeout=5)
        status["cron"] = r.stdout.decode() if r.returncode == 0 else ""
    except:
        status["cron"] = ""

    # Public URLs
    urls = []
    for path in ["/root/evo-ai/data/telegra_urls.txt",
                 "/root/evo-ai/data/auto_publish_urls.txt",
                 "/root/evo-ai/data/github_issue_urls.txt"]:
        if os.path.exists(path):
            with open(path) as f:
                urls += [l.strip() for l in f if l.strip() and not l.startswith("=") and not l.startswith("#")]
    status["public_urls"] = urls
    status["public_urls_count"] = len(urls)

    return status


# Flask route registration
def register_routes(app):
    @app.route("/workflow")
    def workflow():
        html, code = render_workflow_page()
        return html, code

    @app.route("/milestones")
    def milestones():
        html, code = render_milestones_page()
        return html, code

    @app.route("/api/workflow/status")
    def workflow_status():
        return render_status_json(), 200


if __name__ == "__main__":
    print("Testing routes...")
    html, code = render_workflow_page()
    print(f"workflow: {code}, {len(html)} bytes")
    html, code = render_milestones_page()
    print(f"milestones: {code}, {len(html)} bytes")
    s = render_status_json()
    print(f"status: {json.dumps({k: v for k, v in s.items() if k not in ['nodes', 'accounts', 'cron', 'public_urls']}, indent=2)[:500]}")