"""
distributed/docs_routes.py
---------------------------
Serve project documentation (PROPOSAL, ROADMAP, DEPLOY) at public URLs
"""

import os
from flask import send_file, abort

PROJECT_ROOT = "/root/evo-ai"

DOCS = {
    "proposal": f"{PROJECT_ROOT}/PROPOSAL.md",
    "roadmap": f"{PROJECT_ROOT}/ROADMAP.md",
    "deploy": f"{PROJECT_ROOT}/DEPLOY.md",
    "readme": f"{PROJECT_ROOT}/README.md",
}


def render_md(md_text):
    """Minimal markdown → HTML"""
    import html
    lines = md_text.split("\n")
    out = []
    in_code = False
    in_list = False
    for line in lines:
        # Code fences
        if line.startswith("```"):
            if in_code:
                out.append("</pre>")
                in_code = False
            else:
                out.append('<pre style="background:#0d0d0d;padding:12px;border-radius:4px;overflow-x:auto;color:#00d4aa;">')
                in_code = True
            continue
        if in_code:
            out.append(html.escape(line))
            continue
        # Headings
        if line.startswith("# "):
            if in_list: out.append("</ul>"); in_list = False
            out.append(f'<h1 style="color:#ff4500;border-bottom:2px solid #ff4500;padding-bottom:8px;">{html.escape(line[2:])}</h1>')
        elif line.startswith("## "):
            if in_list: out.append("</ul>"); in_list = False
            out.append(f'<h2 style="color:#00d4aa;border-bottom:1px solid #333;padding-bottom:6px;margin-top:30px;">{html.escape(line[3:])}</h2>')
        elif line.startswith("### "):
            if in_list: out.append("</ul>"); in_list = False
            out.append(f'<h3 style="color:#ff4500;">{html.escape(line[4:])}</h3>')
        elif line.startswith("- ") or line.startswith("* "):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.startswith("|"):
            if in_list: out.append("</ul>"); in_list = False
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if not all(set(c) <= set("-: ") for c in cells):
                out.append("<tr>" + "".join(f"<td style='padding:6px 12px;border:1px solid #333;'>{html.escape(c)}</td>" for c in cells) + "</tr>")
        elif line.strip() == "":
            if in_list: out.append("</ul>"); in_list = False
            out.append("<br>")
        elif line.startswith("**") and line.endswith("**"):
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<p><strong>{html.escape(line[2:-2])}</strong></p>")
        else:
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<p>{html.escape(line)}</p>")
    if in_list: out.append("</ul>")
    if in_code: out.append("</pre>")
    return "\n".join(out)


def make_page(title, md_text, color="#ff4500"):
    """Wrap markdown in styled HTML page"""
    body = render_md(md_text)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title} - EVO-AI</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0a0a0a; color: #e0e0e0; max-width: 900px; margin: 0 auto; padding: 40px 20px; line-height: 1.6; }}
  h1 {{ color: {color}; }}
  h2 {{ color: #00d4aa; }}
  code {{ background: #272729; padding: 2px 6px; border-radius: 3px; color: #ff4500; font-family: monospace; }}
  pre {{ background: #0d0d0d; padding: 12px; border-radius: 4px; overflow-x: auto; color: #00d4aa; }}
  a {{ color: #ff4500; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  table {{ border-collapse: collapse; margin: 16px 0; }}
  td, th {{ border: 1px solid #333; padding: 6px 12px; }}
  hr {{ border: 0; border-top: 1px solid #333; margin: 30px 0; }}
  .nav {{ background: #1a1a1b; padding: 12px 20px; border-radius: 4px; margin-bottom: 20px; }}
  .nav a {{ margin-right: 20px; color: #00d4aa; }}
</style>
</head>
<body>

<div class="nav">
  <a href="/">🏠 Home</a>
  <a href="/proposal">💰 Proposal</a>
  <a href="/roadmap">🗺️ Roadmap</a>
  <a href="/deploy">🚀 Deploy</a>
  <a href="/donate">💳 Donate</a>
  <a href="/api/info">📡 API</a>
  <a href="/.well-known/agent.json">🤖 A2A</a>
</div>

{body}

<hr>
<p style="text-align:center;color:#666;">
EVO-AI Project · <a href="/proposal">Donate</a> · <a href="/api/info">API</a> · <a href="https://www.moltbook.com/u/evo-ai">Moltbook</a>
</p>

</body>
</html>"""


def register_docs_routes(app):
    """Register all docs routes"""

    @app.route("/docs", methods=["GET"])
    def docs_index():
        return make_page("Documentation", """# EVO-AI Documentation

Welcome to the EVO-AI documentation hub.

## Available Documents

- [💰 Proposal](/proposal) - For donors & collaborators
- [🗺️ Roadmap](/roadmap) - Technical roadmap & milestones
- [🚀 Deploy](/deploy) - Run your own EVO-AI node

## Quick Links

- [HTTP API](/api/info) - 12 public endpoints
- [A2A Manifest](/.well-known/agent.json) - Agent discovery
- [WebSocket](/ws) - Real-time messaging
- [Donate](/donate) - Support the project
- [Moltbook](https://www.moltbook.com/u/evo-ai) - Social profile
- [OpenAgents](http://47.253.174.153:8700) - Public network (network: evo-ai-public-network-2026)
""")

    @app.route("/proposal", methods=["GET"])
    def docs_proposal():
        path = DOCS["proposal"]
        if not os.path.exists(path):
            return make_page("Proposal", "# Proposal\n\nComing soon.", "#ff4500")
        with open(path) as f:
            md = f.read()
        return make_page("Proposal", md, "#ff4500")

    @app.route("/roadmap", methods=["GET"])
    def docs_roadmap():
        path = DOCS["roadmap"]
        if not os.path.exists(path):
            return make_page("Roadmap", "# Roadmap\n\nComing soon.", "#00d4aa")
        with open(path) as f:
            md = f.read()
        return make_page("Roadmap", md, "#00d4aa")

    @app.route("/deploy", methods=["GET"])
    def docs_deploy():
        path = DOCS["deploy"]
        if not os.path.exists(path):
            return make_page("Deploy", "# Deploy\n\nComing soon.", "#3b82f6")
        with open(path) as f:
            md = f.read()
        return make_page("Deploy", md, "#3b82f6")

    @app.route("/readme", methods=["GET"])
    def docs_readme():
        path = DOCS["readme"]
        if not os.path.exists(path):
            return make_page("README", "# README\n\nComing soon.", "#ff4500")
        with open(path) as f:
            md = f.read()
        return make_page("README", md, "#ff4500")

    @app.route("/api/docs", methods=["GET"])
    def api_docs():
        """API doc listing"""
        from flask import jsonify
        return jsonify({
            "docs": {
                "proposal": "http://47.253.174.153:80/proposal",
                "roadmap": "http://47.253.174.153:80/roadmap",
                "deploy": "http://47.253.174.153:80/deploy",
                "readme": "http://47.253.174.153:80/readme",
                "donate": "http://47.253.174.153:80/donate",
            },
            "external": {
                "huggingface_space_ready": "see /workspace/evo-ai/hf_space/",
                "moltbook": "https://www.moltbook.com/u/evo-ai",
                "openagents": "47.253.174.153:8700",
            },
            "raw_markdown": {
                "proposal": "/proposal.md",
                "roadmap": "/roadmap.md",
                "deploy": "/deploy.md",
            }
        })

    @app.route("/proposal.md", methods=["GET"])
    def proposal_raw():
        path = DOCS["proposal"]
        if not os.path.exists(path):
            abort(404)
        return send_file(path, mimetype="text/markdown")

    @app.route("/roadmap.md", methods=["GET"])
    def roadmap_raw():
        path = DOCS["roadmap"]
        if not os.path.exists(path):
            abort(404)
        return send_file(path, mimetype="text/markdown")

    @app.route("/deploy.md", methods=["GET"])
    def deploy_raw():
        path = DOCS["deploy"]
        if not os.path.exists(path):
            abort(404)
        return send_file(path, mimetype="text/markdown")