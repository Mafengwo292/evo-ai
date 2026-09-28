"""Leaderboard route - clean and tested."""

LEADERBOARD_HTML = """<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>EVO-AI Leaderboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, sans-serif; background: #0a0e1a; color: #d8e2ff; padding: 20px; }
.container { max-width: 900px; margin: 0 auto; }
h1 { color: #6bd9ff; margin-bottom: 10px; }
.subtitle { color: #8b9bc4; margin-bottom: 30px; }
.hero { background: rgba(107,217,255,0.1); padding: 30px; border-radius: 12px; border: 1px solid rgba(107,217,255,0.3); margin-bottom: 30px; }
.metric { display: inline-block; margin-right: 30px; }
.metric-label { color: #8b9bc4; font-size: 12px; text-transform: uppercase; }
.metric-num { color: #6bd9ff; font-size: 2.5em; font-weight: bold; }
.progress-bar { width: 100%; height: 30px; background: rgba(255,255,255,0.1); border-radius: 15px; overflow: hidden; margin: 15px 0; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #6bd9ff, #b794f6); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #0a0e1a; }
.cta { background: linear-gradient(135deg, #6bd9ff, #b794f6); color: #0a0e1a; padding: 20px 30px; border-radius: 12px; text-align: center; margin: 20px 0; }
.cta h2 { margin-bottom: 10px; }
.cta code { background: rgba(0,0,0,0.2); padding: 8px 12px; border-radius: 6px; display: inline-block; margin: 5px; font-family: monospace; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th { background: rgba(107,217,255,0.2); padding: 12px; text-align: left; color: #6bd9ff; }
td { padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); }
a { color: #6bd9ff; text-decoration: none; }
</style>
</head><body>
<div class="container">
<h1>EVO-AI Leaderboard</h1>
<p class="subtitle">Distributed self-evolving language model network</p>

<div class="hero">
<div class="metric"><div class="metric-label">Generation</div><div class="metric-num">__GEN__</div></div>
<div class="metric"><div class="metric-label">Fitness</div><div class="metric-num">__FIT__</div></div>
<div class="metric"><div class="metric-label">Active Nodes</div><div class="metric-num">__NODES__</div></div>
<div class="progress-bar">
<div class="progress-fill" style="width: __PCT__%">__PCT__% to target 0.5</div>
</div>
</div>

<div class="cta">
<h2>Join the federation</h2>
<p style="margin-bottom: 15px;">Run your own (1+lambda)-ES node in 10 seconds:</p>
<code>pip install numpy requests</code><br>
<code>curl -sSL https://paste.rs/yUB9t -o evo.py</code><br>
<code>python evo.py --node-id YOUR-NAME</code>
</div>

<h2 style="margin-top: 30px; color: #6bd9ff;">Active Nodes</h2>
<table>
<thead><tr><th>Node ID</th><th>Balance (EVO)</th><th>Capabilities</th></tr></thead>
<tbody>__TABLE__</tbody>
</table>
</div>
</body></html>"""


def render_leaderboard():
    """Render leaderboard with live data."""
    import json, time, urllib.request
    
    # Get latest evolution
    fitness = 0.0
    gen = 0
    try:
        with open('/root/evo-ai/data/light_evo_log.jsonl') as f:
            lines = f.readlines()
        if lines:
            latest = json.loads(lines[-1])
            fitness = latest.get('fitness', 0.0)
            gen = latest.get('generation', 0)
    except:
        pass
    
    # Get nodes
    nodes = []
    try:
        with urllib.request.urlopen('http://127.0.0.1:8765/api/evo/nodes', timeout=5) as resp:
            data = json.loads(resp.read())
            nodes = data.get('nodes', [])
    except:
        pass
    
    # Build table
    rows = ''
    for n in nodes[:30]:
        nid = str(n.get('node_id', '?'))[:30]
        bal = n.get('balance', 0)
        caps = ', '.join(n.get('capabilities', [])[:3])
        rows += '<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (nid, f'{bal:,}', caps)
    
    pct = (fitness / 0.5) * 100 if fitness > 0 else 0
    
    html = LEADERBOARD_HTML
    html = html.replace('__GEN__', str(gen))
    html = html.replace('__FIT__', f'{fitness:.4f}')
    html = html.replace('__NODES__', str(len(nodes)))
    html = html.replace('__PCT__', f'{pct:.1f}')
    html = html.replace('__TABLE__', rows if rows else '<tr><td colspan="3">No nodes yet</td></tr>')
    
    return html
