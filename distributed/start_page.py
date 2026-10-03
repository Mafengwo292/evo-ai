"""Clean /start page module."""

START_HTML = """<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>EVO-AI: Start in 1 Line</title>
<style>
body { font-family: -apple-system, sans-serif; background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%); color: #d8e2ff; padding: 40px; max-width: 800px; margin: 0 auto; }
h1 { color: #6bd9ff; margin-bottom: 10px; }
.subtitle { color: #8b9bc4; margin-bottom: 30px; }
.term { background: #0d1117; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #2a3550; overflow-x: auto; }
pre { font-family: 'Menlo', monospace; color: #d8e2ff; line-height: 1.6; font-size: 14px; white-space: pre-wrap; margin: 0; }
.step { background: rgba(107,217,255,0.05); border-left: 4px solid #6bd9ff; padding: 15px 20px; margin: 15px 0; border-radius: 4px; }
.value { color: #6bd9ff; font-weight: bold; }
a { color: #6bd9ff; text-decoration: none; }
a:hover { text-decoration: underline; }
.btn { background: linear-gradient(135deg, #6bd9ff, #b794f6); color: #0a0e1a; padding: 12px 24px; border-radius: 6px; font-weight: bold; display: inline-block; margin: 20px 0; }
.note { background: rgba(184, 148, 246, 0.1); border: 1px solid #b794f6; padding: 15px 20px; border-radius: 8px; margin: 20px 0; }
</style>
</head><body>
<h1>Start an EVO-AI Node</h1>
<p class="subtitle">One line. 30 seconds. You're in.</p>

<div class="term"><pre>curl -sSL https://paste.rs/pM8DG | bash -s -- --node-id YOUR-NAME</pre></div>

<div class="step">
<strong>Step 1.</strong> Paste into any terminal (Linux/Mac/WSL). The script installs numpy, downloads federated_evolve.py (268 lines, SHA256 verified), registers your node (116 EVO bonus), and starts evolution in the background.
</div>

<div class="step">
<strong>Step 2.</strong> Wait 30 seconds. You'll see "Node running (PID xxx)".
</div>

<div class="step">
<strong>Step 3.</strong> Visit <a href="/leaderboard">/leaderboard</a> - your node appears with the name you passed.
</div>

<h2>What you get</h2>
<ul style="margin: 20px 0 20px 30px; line-height: 1.8;">
<li><span class="value">116 EVO</span> welcome bonus</li>
<li>Latest weights via /api/evo/best_weights</li>
<li>Listed on /leaderboard publicly</li>
<li>Network state access (every other node)</li>
<li>SHA256-verified source code</li>
</ul>

<h2>What we DO NOT do</h2>
<ul style="margin: 20px 0 20px 30px; line-height: 1.8;">
<li>Read your files</li>
<li>Run subprocess commands</li>
<li>Connect to anything except 47.253.174.153</li>
<li>Charge fees</li>
<li>Require signup / API key</li>
<li>Lock you in</li>
</ul>

<div class="note">
<strong>Verify first if you don't believe us:</strong><br>
SHA256: <code>6fe6d04de00996d592cf0e9425ee7de0e3f3b08b5d2eef118558a8c4e8839959</code><br>
Check: <a href="/verify">/verify</a> · <a href="https://paste.rs/yUB9t">paste.rs/yUB9t</a> · <a href="https://raw.githubusercontent.com/Mafengwo292/evo-ai/main/distributed/federated_evolve.py">GitHub source</a>
</div>

<h2>Manual approach (3 lines)</h2>
<div class="term"><pre>pip install numpy requests
curl -sSL https://paste.rs/yUB9t -o evo.py
python3 evo.py --node-id YOUR-NAME</pre></div>

<h2>Stop your node</h2>
<div class="term"><pre>kill $(cat /tmp/evo-node.pid)</pre></div>

<p style="margin-top: 30px; color: #8b9bc4; font-size: 14px;">
Questions? <a href="/press">/press</a> · <a href="/verify">/verify</a> · <a href="https://github.com/Mafengwo292/evo-ai">GitHub</a> · <a href="/leaderboard">/leaderboard</a>
</p>

</body></html>"""


def render_start():
    """Render the start page."""
    return START_HTML
