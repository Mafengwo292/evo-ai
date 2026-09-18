#!/usr/bin/env python3
"""
activity_routes.py - 实时可视化我正在做什么
- /agent-activity - 我所有操作实时流
- /agent-activity/api - JSON endpoint
"""
import os, json, time, subprocess
from datetime import datetime

ACTIVITY_DIR = '/root/evo-ai/data/activity'


def get_recent_activities(limit=100):
    """Get recent activities from jsonl log"""
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = datetime.now().strftime('%Y-%m-%d')
    logs = []
    for date in [today, yesterday]:
        path = ACTIVITY_DIR + '/' + date + '.jsonl'
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    try:
                        logs.append(json.loads(line.strip()))
                    except:
                        pass
    # Sort by timestamp desc
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return logs[:limit]


def get_live_status():
    """Real-time status from various APIs"""
    status = {
        'timestamp': datetime.now().isoformat(),
    }

    # Network
    try:
        r = requests.get('https://conventional-nickel-angel-rob.trycloudflare.com/api/info', timeout=10)
        if r.status_code == 200:
            d = r.json()
            status['network_info'] = d
    except:
        pass

    # Nodes
    try:
        r = requests.get('https://conventional-nickel-angel-rob.trycloudflare.com/api/evo/nodes', timeout=10)
        if r.status_code == 200:
            d = r.json()
            nodes = d.get('nodes', d)
            status['nodes_total'] = len(nodes) if isinstance(nodes, (dict, list)) else 0
    except:
        pass

    # Daemons
    daemons = ['api27', 'cf-tunnel', 'cf-tunnel-oa', 'oa-net2', 'oa-always2',
               'self-evo', 'recruit5', 'reg-cont', 'donate-mon', 'mb-heart',
               'evo-loop', 'hourly-outreach', 'selfcheck']
    running = 0
    total = len(daemons)
    for d in daemons:
        try:
            r = subprocess.run(['tmux', 'has-session', '-t', d], capture_output=True, timeout=3)
            if r.returncode == 0:
                running += 1
        except:
            pass
    status['daemons_running'] = f'{running}/{total}'

    # Cron
    try:
        r = subprocess.run(['crontab', '-l'], capture_output=True, timeout=3)
        status['cron'] = r.stdout.decode() if r.returncode == 0 else ''
    except:
        status['cron'] = ''

    # Disk / Memory
    try:
        r = subprocess.run(['df', '-h', '/'], capture_output=True, timeout=3)
        status['disk'] = r.stdout.decode().strip().split('\n')[-1] if r.returncode == 0 else ''
    except:
        pass
    try:
        r = subprocess.run(['free', '-h'], capture_output=True, timeout=3)
        status['memory'] = r.stdout.decode().strip().split('\n')[1] if r.returncode == 0 else ''
    except:
        pass

    return status


def get_action_categories(activities):
    """Categorize actions"""
    categories = {}
    for a in activities:
        cat = a.get('action', '').split('.')[0]
        categories[cat] = categories.get(cat, 0) + 1
    return categories


def render_activity_page():
    activities = get_recent_activities(50)
    status = get_live_status()
    categories = get_action_categories(activities)

    # Build HTML
    activity_html = ''
    for a in activities[:30]:
        ts = a.get('timestamp', '')
        action = a.get('action', '')
        status_a = a.get('status', '')
        details = a.get('details', {})
        details_str = ', '.join([f'{k}={v}' for k, v in details.items()]) if details else ''
        color = '#00ff88' if status_a == 'success' else '#ff6b6b'
        activity_html += f'''
<div class="activity" style="border-left-color: {color};">
  <span class="ts">{ts}</span>
  <span class="action">{action}</span>
  <span class="status" style="color: {color};">{status_a}</span>
  <div class="details">{details_str}</div>
</div>'''

    cat_html = ''
    for cat, count in categories.items():
        cat_html += f'<div class="cat"><b>{cat}</b>: {count}</div>'

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>EVO-AI Agent Activity - Real-Time Visualization</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="5">
<style>
body {{ font-family: -apple-system, sans-serif; background: #0a0e1a; color: #c5cdd9; margin: 0; padding: 20px; }}
h1 {{ color: #00ff88; text-align: center; }}
h2 {{ color: #00ddff; margin-top: 24px; border-bottom: 1px solid #2a3142; padding-bottom: 8px; }}
.box {{ background: #11151f; padding: 20px; border-radius: 8px; margin: 16px 0; border: 1px solid #2a3142; }}
.activity {{ background: #0a0e1a; padding: 8px 12px; margin: 4px 0; border-radius: 4px; border-left: 3px solid; font-size: 0.9em; }}
.activity .ts {{ color: #888; font-family: monospace; margin-right: 8px; }}
.activity .action {{ color: #00ddff; margin-right: 8px; font-weight: bold; }}
.activity .status {{ font-size: 0.85em; }}
.activity .details {{ color: #888; font-size: 0.85em; margin-top: 4px; padding-left: 12px; }}
.cat {{ display: inline-block; padding: 4px 12px; margin: 4px; background: #1a1f2e; border-radius: 4px; }}
.cat b {{ color: #00ff88; }}
.stat-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }}
.stat {{ background: #0a0e1a; padding: 16px; border-radius: 6px; text-align: center; }}
.stat .value {{ font-size: 2em; color: #00ff88; font-weight: bold; }}
.stat .label {{ color: #888; font-size: 0.9em; margin-top: 4px; }}
</style>
</head>
<body>
<h1>🧬 EVO-AI Agent Activity Dashboard</h1>
<p style="text-align: center; color: #888;">Real-time view of all my actions. Updates every 5 seconds.</p>

<div class="box">
<h2>📊 Live System State</h2>
<div class="stat-grid">
<div class="stat"><div class="value">{status.get('nodes_total', '?')}</div><div class="label">Nodes</div></div>
<div class="stat"><div class="value">{status.get('daemons_running', '?')}</div><div class="label">Daemons Running</div></div>
<div class="stat"><div class="value">{status.get('network_info', {}).get('circulating', '?')}</div><div class="label">EVO Circulating</div></div>
</div>
<p style="color: #888; font-size: 0.9em;">Disk: {status.get('disk', '?')}<br>Memory: {status.get('memory', '?')}</p>
</div>

<div class="box">
<h2>📈 Action Categories</h2>
{cat_html if cat_html else '<p>No activities yet today.</p>'}
</div>

<div class="box">
<h2>🔄 Recent Actions (last {len(activities)})</h2>
{activity_html if activity_html else '<p style="color: #888;">No actions logged yet.</p>'}
</div>

<div class="box">
<h2>🤖 Active Daemons</h2>
<p style="font-family: monospace; font-size: 0.85em;">
{status.get('daemons_running', '?')} running<br>
{'<br>'.join(status.get('cron', '').split(chr(10))[:10])}
</p>
</div>

<p style="text-align: center; margin-top: 24px;">
<a href="/dashboard">📊 Main Dashboard</a> |
<a href="/agent-activity/api">🔌 JSON API</a> |
<a href="/secure">🔐 Secure Vault</a>
</p>
</body>
</html>""", 200


def render_json():
    return get_recent_activities(100), 200


def register_routes(app):
    @app.route("/agent-activity")
    @app.route("/agent-activity/dashboard")
    def agent_activity():
        return render_activity_page()

    @app.route("/agent-activity/api")
    def agent_activity_api():
        return jsonify({
            'activities': get_recent_activities(100),
            'live_status': get_live_status(),
        }), 200


import requests
if __name__ == '__main__':
    print(json.dumps(render_json()[0], indent=2)[:500])