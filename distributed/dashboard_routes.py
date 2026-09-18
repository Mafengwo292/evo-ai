"""
distributed/dashboard_routes.py
--------------------------------
Real-time visualization dashboard for EVO-AI.

All data is fetched live from the API - no caching, no hardcoded values.
Updates every 5 seconds via JavaScript fetch.

Pages:
- /dashboard  - Full project dashboard
- /live       - Lightweight live status page
"""

import os
from flask import jsonify, request


def register_routes(app):
    """Register dashboard routes"""

    @app.route("/dashboard", methods=["GET"])
    def dashboard_page():
        """Full real-time dashboard"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>EVO-AI Live Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0a0a0a; color: #e6e6e6; margin: 0; padding: 20px; }
  .container { max-width: 1400px; margin: 0 auto; }
  .header { background: linear-gradient(135deg, #1a1a1b, #272729); padding: 24px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #343536; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
  .header h1 { color: #ff4500; margin: 0; font-size: 2em; }
  .header .subtitle { color: #888; font-size: 0.9em; }
  .live-indicator { display: inline-flex; align-items: center; gap: 6px; background: #1a3a1a; padding: 6px 12px; border-radius: 20px; font-size: 0.85em; color: #4ade80; }
  .live-indicator .dot { width: 8px; height: 8px; background: #4ade80; border-radius: 50%; animation: pulse 2s infinite; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 20px; }
  .card { background: #1a1a1b; padding: 20px; border-radius: 8px; border: 1px solid #343536; }
  .card h3 { margin: 0 0 12px 0; color: #00d4aa; font-size: 0.9em; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #333; padding-bottom: 8px; }
  .stat-big { font-size: 2em; font-weight: bold; color: #ff4500; }
  .stat-medium { font-size: 1.4em; color: #00d4aa; }
  .stat-small { font-size: 1em; color: #e6e6e6; }
  .stat-label { font-size: 0.85em; color: #888; margin-top: 4px; }
  .progress-bar { background: #343536; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 8px; }
  .progress-bar-fill { background: linear-gradient(90deg, #ff4500, #ff8c00); height: 100%; transition: width 0.5s; }
  table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
  td, th { padding: 8px 12px; text-align: left; border-bottom: 1px solid #343536; }
  th { color: #00d4aa; font-weight: 600; }
  code { background: #272729; padding: 2px 6px; border-radius: 3px; color: #ff4500; font-family: monospace; font-size: 0.9em; }
  .pill { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600; }
  .pill-up { background: #1a3a1a; color: #4ade80; }
  .pill-down { background: #3a1a1a; color: #f87171; }
  .pill-warn { background: #3a3a1a; color: #fbbf24; }
  .activity-feed { max-height: 300px; overflow-y: auto; font-size: 0.85em; }
  .activity-item { padding: 8px 12px; border-left: 2px solid #ff4500; margin: 4px 0; background: #272729; border-radius: 4px; font-family: monospace; }
  .footer { text-align: center; margin-top: 30px; color: #666; font-size: 0.85em; }
  .footer a { color: #ff4500; margin: 0 8px; }
  .update-time { color: #666; font-size: 0.8em; }
  .error { color: #f87171; }
</style>
</head>
<body>
<div class="container">

<div class="header">
  <div>
    <h1>🧬 EVO-AI Live Dashboard</h1>
    <div class="subtitle">Distributed Self-Evolving AI · Real-time data, no caching, no fabrication</div>
  </div>
  <div>
    <div class="live-indicator"><span class="dot"></span>LIVE</div>
    <div class="update-time" id="lastUpdate">Last update: -</div>
  </div>
</div>

<!-- Section 1: Token Stats -->
<div class="grid">
  <div class="card">
    <h3>🪙 EVO Total Supply (Hard Cap)</h3>
    <div class="stat-big" id="totalSupply">-</div>
    <div class="stat-label">EVO · 永不增发</div>
  </div>
  <div class="card">
    <h3>📊 Minted</h3>
    <div class="stat-medium" id="minted">-</div>
    <div class="progress-bar"><div class="progress-bar-fill" id="mintedBar" style="width: 0%"></div></div>
    <div class="stat-label" id="mintedPct">- of total</div>
  </div>
  <div class="card">
    <h3>🔥 Burned</h3>
    <div class="stat-medium" id="burned">-</div>
    <div class="stat-label">Deflationary (0.1% per tx)</div>
  </div>
  <div class="card">
    <h3>💧 Circulating</h3>
    <div class="stat-medium" id="circulating">-</div>
    <div class="stat-label">= Minted − Burned</div>
  </div>
</div>

<!-- Section 2: Network & Donations -->
<div class="grid">
  <div class="card">
    <h3>🖥️ Active Nodes</h3>
    <div class="stat-big" id="nodes">-</div>
    <div class="stat-label" id="nodeRewards">Total rewards paid: -</div>
  </div>
  <div class="card">
    <h3>👥 Accounts</h3>
    <div class="stat-big" id="accounts">-</div>
    <div class="stat-label">All wallets on EVO ledger</div>
  </div>
  <div class="card">
    <h3>💰 Donations (CNY)</h3>
    <div class="stat-big" id="donations">¥-</div>
    <div class="stat-label" id="donors">- donors</div>
  </div>
  <div class="card">
    <h3>🧠 Model</h3>
    <div class="stat-medium" id="modelParams">-</div>
    <div class="stat-label" id="modelInfo">-</div>
  </div>
</div>

<!-- Section 3: Endpoints Health -->
<div class="card" style="margin-bottom: 20px;">
  <h3>🏥 Endpoint Health</h3>
  <table id="endpointsTable">
    <thead><tr><th>Endpoint</th><th>Status</th><th>Response (ms)</th></tr></thead>
    <tbody id="endpointsBody"></tbody>
  </table>
</div>

<!-- Section 4: Nodes List -->
<div class="card" style="margin-bottom: 20px;">
  <h3>📋 Registered Nodes</h3>
  <table>
    <thead><tr><th>Node ID</th><th>Address</th><th>Endpoint</th><th>Epochs</th><th>Rewarded (EVO)</th><th>Status</th></tr></thead>
    <tbody id="nodesBody"></tbody>
  </table>
</div>

<!-- Section 5: Top Accounts -->
<div class="card" style="margin-bottom: 20px;">
  <h3>🏆 Top Wallets</h3>
  <table>
    <thead><tr><th>Address</th><th>Name</th><th>Type</th><th>Balance (EVO)</th></tr></thead>
    <tbody id="accountsBody"></tbody>
  </table>
</div>

<!-- Section 6: Activity Feed -->
<div class="card" style="margin-bottom: 20px;">
  <h3>📡 Recent Activity</h3>
  <div class="activity-feed" id="activityFeed">
    <div class="activity-item">⏳ Initializing...</div>
  </div>
</div>

<div class="footer">
  <a href="/">🏠 Home</a> · <a href="/token">🪙 Token</a> · <a href="/donate">💰 Donate</a> · <a href="/api/info">📡 API</a> · <a href="/api/join/instructions">🚀 Join</a>
  <br><br>

  <div style="margin: 20px 0; padding: 16px; background: #1a1a1b; border-radius: 8px; border: 1px solid #343536;">
    <h3 style="color:#00d4aa; margin: 0 0 12px 0;">🌐 Registered on External Networks (6 platforms)</h3>
    <a href='https://basedagents.ai/agent/EVO-AI' target='_blank' style="display:inline-block; margin: 8px;">
      <img src='https://api.basedagents.ai/v1/agents/ag_6ybSEDkZThZXudTVCKfrsTT2uxu26Kpf4kaMsZ2xZuka/badge' alt='BasedAgents' style="height: 28px;" />
    </a>
    <a href='https://api.agentthreads.dev/api/v1/agents/EVO-AI' target='_blank' style="display:inline-block; margin: 8px; padding: 6px 12px; background:#272729; color:#00d4aa; border-radius:4px; text-decoration:none; font-weight:bold;">
      AgentThreads
    </a>
    <a href='https://a2aregistry.org/agent/427e26db-25ad-41ae-ae73-cc8998b54b29' target='_blank' style="display:inline-block; margin: 8px; padding: 6px 12px; background:#272729; color:#ff4500; border-radius:4px; text-decoration:none; font-weight:bold;">
      A2ARegistry
    </a>
    <a href='https://agent-directory-frontend.vercel.app/' target='_blank' style="display:inline-block; margin: 8px; padding: 6px 12px; background:#272729; color:#10b981; border-radius:4px; text-decoration:none; font-weight:bold;">
      AgentDirectory
    </a>
    <a href='https://agentmarket.space' target='_blank' style="display:inline-block; margin: 8px; padding: 6px 12px; background:#272729; color:#f59e0b; border-radius:4px; text-decoration:none; font-weight:bold;">
      AgentMarket (100 credits)
    </a>
    <a href='https://clawhub.ai' target='_blank' style="display:inline-block; margin: 8px; padding: 6px 12px; background:#272729; color:#8b5cf6; border-radius:4px; text-decoration:none; font-weight:bold;">
      ClawHub
    </a>
  </div>

  <span style="color:#888">All data fetched live via <code>fetch()</code> from real API endpoints. No hardcoded values. No fabrication.</span>
  <br>
  <span style="color:#666">EVO-AI · Open source (MIT) · <span id="version">-</span></span>
</div>

</div>

<script>
const API_BASE = window.location.origin;
const REFRESH_MS = 5000;
let activityLog = [];
let cycleCount = 0;

function log(msg, type='info') {
  const t = new Date().toISOString().substr(11, 8);
  activityLog.unshift(`[${t}] ${msg}`);
  if (activityLog.length > 30) activityLog.pop();
  const feed = document.getElementById('activityFeed');
  feed.innerHTML = activityLog.map(m => `<div class="activity-item">${m}</div>`).join('');
}

function fmt(n, decimals=2) {
  if (n == null) return '-';
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function fmtInt(n) {
  if (n == null) return '-';
  return Number(n).toLocaleString('en-US');
}

async function fetchJSON(url, opts) {
  try {
    const start = performance.now();
    const r = await fetch(url, opts);
    const ms = Math.round(performance.now() - start);
    const ok = r.ok;
    let data = null;
    try { data = await r.json(); } catch (e) {}
    return { ok, status: r.status, ms, data };
  } catch (e) {
    return { ok: false, error: e.message, ms: -1, data: null };
  }
}

async function loadEVOSTats() {
  const { ok, data } = await fetchJSON(`${API_BASE}/api/evo/stats`);
  if (!ok || !data) { log('❌ /api/evo/stats failed'); return; }

  document.getElementById('totalSupply').textContent = fmtInt(data.total_supply_evo) + ' EVO';
  document.getElementById('minted').textContent = fmt(data.minted, 2) + ' EVO';
  document.getElementById('burned').textContent = fmt(data.burned, 2) + ' EVO';
  document.getElementById('circulating').textContent = fmt(data.circulating, 2) + ' EVO';

  const pct = (data.minted / data.total_supply_evo) * 100;
  document.getElementById('mintedBar').style.width = pct.toFixed(6) + '%';
  document.getElementById('mintedPct').textContent = pct.toFixed(8) + '% of total supply';

  document.getElementById('nodes').textContent = fmtInt(data.nodes);
  document.getElementById('accounts').textContent = fmtInt(data.accounts);
  document.getElementById('nodeRewards').textContent = 'Total rewards paid: ' + fmt(data.total_node_rewards, 2) + ' EVO';
}

async function loadDonations() {
  const { ok, data } = await fetchJSON(`${API_BASE}/api/donate/stats`);
  if (!ok || !data) { log('❌ /api/donate/stats failed'); return; }
  document.getElementById('donations').textContent = '¥' + fmt(data.total_amount || 0, 2);
  document.getElementById('donors').textContent = fmtInt(data.total_count || 0) + ' donors';
  if ((data.total_count || 0) > 0) {
    log(`💰 Donation update: ¥${fmt(data.total_amount)} CNY from ${data.total_count} donors`);
  }
}

async function loadModel() {
  const { ok, data } = await fetchJSON(`${API_BASE}/api/info`);
  if (!ok || !data) { log('❌ /api/info failed'); return; }
  document.getElementById('modelParams').textContent = fmtInt(data.model?.params) + ' params';
  document.getElementById('modelInfo').textContent = `Vocab ${data.model?.vocab} · ${(data.uptime_seconds/3600).toFixed(1)}h uptime`;
  document.getElementById('version').textContent = data.version || 'EVO-AI v1.0';
}

async function loadNodes() {
  const { ok, data } = await fetchJSON(`${API_BASE}/api/evo/nodes`);
  if (!ok || !data) return;
  const nodes = data.nodes || [];
  const body = document.getElementById('nodesBody');
  if (nodes.length === 0) {
    body.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#666;">No nodes registered</td></tr>';
    return;
  }
  body.innerHTML = nodes.map(n => {
    const status = (Date.now() - new Date(n.last_heartbeat || 0).getTime() < 24*3600*1000)
      ? '<span class="pill pill-up">ACTIVE</span>'
      : '<span class="pill pill-down">STALE</span>';
    return `<tr>
      <td><b>${n.node_id}</b></td>
      <td><code>${n.address}</code></td>
      <td>${n.endpoint}</td>
      <td>${n.epochs_completed}</td>
      <td>${fmt(n.total_rewarded_evo, 2)}</td>
      <td>${status}</td>
    </tr>`;
  }).join('');
}

async function loadAccounts() {
  const { ok, data } = await fetchJSON(`${API_BASE}/api/evo/accounts`);
  if (!ok || !data) return;
  const accs = (data.accounts || []).slice(0, 10);
  const body = document.getElementById('accountsBody');
  if (accs.length === 0) {
    body.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#666;">No accounts</td></tr>';
    return;
  }
  body.innerHTML = accs.map(a => `<tr>
    <td><code>${a.address}</code></td>
    <td>${a.name}</td>
    <td><span class="pill pill-warn">${a.type}</span></td>
    <td>${fmt(a.balance_evo, 2)}</td>
  </tr>`).join('');
}

async function checkEndpoints() {
  const endpoints = [
    '/api/info', '/api/evo/stats', '/api/donate/stats',
    '/token', '/donate', '/api/join/instructions', '/api/evo/nodes',
    '/api/evo/accounts', '/.well-known/agent.json',
    '/proposal', '/roadmap', '/deploy'
  ];
  const results = await Promise.all(endpoints.map(async ep => {
    const r = await fetchJSON(API_BASE + ep);
    return { ep, ...r };
  }));
  const body = document.getElementById('endpointsBody');
  body.innerHTML = results.map(r => {
    const status = r.ok ? '<span class="pill pill-up">UP</span>'
                       : `<span class="pill pill-down">DOWN (${r.status || r.error})</span>`;
    return `<tr><td><code>${r.ep}</code></td><td>${status}</td><td>${r.ms} ms</td></tr>`;
  }).join('');

  const upCount = results.filter(r => r.ok).length;
  if (cycleCount % 6 === 0) {
    log(`🏥 Health: ${upCount}/${results.length} endpoints up`);
  }
}

async function cycle() {
  cycleCount++;
  await Promise.all([
    loadEVOSTats(),
    loadDonations(),
    loadModel(),
    loadNodes(),
    loadAccounts(),
    checkEndpoints(),
  ]);
  document.getElementById('lastUpdate').textContent =
    `Last update: ${new Date().toLocaleTimeString()} (cycle ${cycleCount})`;
}

cycle();
log('🟢 Dashboard started');
setInterval(cycle, REFRESH_MS);
</script>
</body>
</html>"""

    @app.route("/live", methods=["GET"])
    def live_page():
        """Lightweight live status (just key metrics)"""
        return """<!DOCTYPE html>
<html><head><title>EVO-AI Live</title>
<meta http-equiv="refresh" content="10">
<style>
body { font-family: monospace; background: #0a0a0a; color: #4ade80; padding: 20px; }
h1 { color: #ff4500; }
.stat { font-size: 2em; margin: 10px 0; }
.refresh { color: #666; font-size: 0.8em; }
</style></head><body>
<h1>🧬 EVO-AI Live Status</h1>
<div class="stat" id="ts">⏳ Loading...</div>
<div class="refresh">Auto-refresh every 10s · Last fetched: <span id="t">-</span></div>
<script>
async function go() {
  try {
    const r = await fetch('/api/evo/stats');
    const d = await r.json();
    document.getElementById('ts').innerHTML =
      `Minted: ${d.minted.toLocaleString()} / ${d.total_supply_evo.toLocaleString()} EVO<br>` +
      `Nodes: ${d.nodes} · Accounts: ${d.accounts} · Rewards: ${d.total_node_rewards.toLocaleString()} EVO`;
    document.getElementById('t').textContent = new Date().toLocaleTimeString();
  } catch(e) { document.getElementById('ts').textContent = '❌ ' + e.message; }
}
go();
setInterval(go, 10000);
</script>
</body></html>"""

    @app.route("/api/dashboard/summary", methods=["GET"])
    def dashboard_summary():
        """JSON summary endpoint for external monitors"""
        try:
            import requests
            evo = requests.get("http://127.0.0.1:8765/api/evo/stats", timeout=3).json()
            donate = requests.get("http://127.0.0.1:8765/api/donate/stats", timeout=3).json()
            info = requests.get("http://127.0.0.1:8765/api/info", timeout=3).json()
            return jsonify({
                "timestamp": __import__('datetime').datetime.now().isoformat(),
                "evo": evo,
                "donations": donate,
                "model": info.get("model"),
                "uptime_seconds": info.get("uptime_seconds"),
            })
        except Exception as e:
            return jsonify({"error": str(e)})