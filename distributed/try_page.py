"""Instant browser-based evolution test. No install needed.
Auto-runs after 2 seconds to test JS execution."""

TRY_HTML = """<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>EVO-AI · Try Now (no install)</title>
<style>
body { font-family: -apple-system, sans-serif; background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%); color: #d8e2ff; padding: 40px; max-width: 800px; margin: 0 auto; }
h1 { color: #6bd9ff; }
pre { background: #0d1117; padding: 20px; border-radius: 8px; overflow-x: auto; border: 1px solid #2a3550; }
.step { background: rgba(107,217,255,0.05); border-left: 4px solid #6bd9ff; padding: 15px 20px; margin: 15px 0; border-radius: 4px; }
.btn { background: linear-gradient(135deg, #6bd9ff, #b794f6); color: #0a0e1a; padding: 12px 24px; border-radius: 6px; font-weight: bold; display: inline-block; cursor: pointer; border: none; font-size: 16px; }
.log { background: #000; color: #6bd9ff; padding: 15px; border-radius: 6px; height: 300px; overflow-y: auto; font-family: Menlo, monospace; font-size: 12px; margin: 15px 0; }
.value { color: #6bd9ff; font-weight: bold; }
a { color: #6bd9ff; }
.auto-note { color: #8b9bc4; font-size: 12px; font-style: italic; }
</style>
</head><body>
<h1>EVO-AI: Try it now (no install)</h1>
<p class="subtitle">Auto-running in <span id="countdown">2</span>s. Or click to start immediately.</p>

<button class="btn" id="startBtn" onclick="runTry()">▶ Run Now</button>

<div id="log" class="log">Waiting to start...</div>

<div class="step">
<strong>What this does:</strong>
<ol>
<li>GET /api/evo/stats (network state)</li>
<li>GET /api/evo/best_weights (latest weights)</li>
<li>POST /api/evo/node/heartbeat (anonymous "I was here")</li>
<li>GET /api/info (server info)</li>
</ol>
All of these are REAL API calls to a real federated network.
</div>

<div class="step">
<strong>If that felt good</strong>, the actual 1-line version (running a real node in your terminal):
<div class="term"><pre>curl -sSL https://paste.rs/pM8DG | bash -s -- --node-id YOUR-NAME</pre></div>
</div>

<div class="step">
<strong>Questions before you run?</strong>
<a href="/verify">/verify</a> · <a href="/press">/press</a> · <a href="/start">/start</a>
</div>

<p class="auto-note">Note: This page auto-runs after 2 seconds. If you see the log fill in, your browser executed JavaScript. If not, your environment blocks scripts.</p>

<script>
let countdownValue = 2;
const countdownEl = document.getElementById('countdown');
const countdownInterval = setInterval(() => {
    countdownValue--;
    countdownEl.textContent = countdownValue;
    if (countdownValue <= 0) {
        clearInterval(countdownInterval);
        runTry();
    }
}, 1000);

async function runTry() {
    clearInterval(countdownInterval);
    const log = document.getElementById('log');
    log.innerHTML = '';
    const ts = () => new Date().toISOString().substring(11, 19);
    const add = (msg) => { log.innerHTML += `[${ts()}] ${msg}\\n`; log.scrollTop = log.scrollHeight; };
    
    add('▶ Starting EVO-AI try-it-now...');
    
    try {
        add('→ GET /api/evo/stats');
        const statsRes = await fetch('/api/evo/stats');
        const stats = await statsRes.json();
        add(`✓ Network: ${stats.agents || stats.total_nodes || 1} agents, fitness ${(stats.best_fitness || 0).toFixed(4)}`);
        
        add('→ GET /api/evo/best_weights');
        const wRes = await fetch('/api/evo/best_weights');
        const weights = await wRes.json();
        add(`✓ Got weights: ${Object.keys(weights).length} params, ${weights.weights?.length || 0} values`);
        
        add('→ POST /api/evo/node/heartbeat (anonymous)');
        const hbRes = await fetch('/api/evo/node/heartbeat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                node_id: 'browser-try-' + Date.now(),
                source: 'try_page_auto',
                user_agent: navigator.userAgent.substring(0, 80)
            })
        });
        const hb = await hbRes.json();
        add(`✓ Heartbeat: ${JSON.stringify(hb).substring(0, 100)}`);
        
        add('→ GET /api/info');
        const infoRes = await fetch('/api/info');
        const info = await infoRes.json();
        add(`✓ Server: ${info.endpoints?.length || '?'} endpoints`);
        
        add('');
        add('🎉 Try-it-now complete!');
        add('');
        add('Run an actual node:');
        add('  curl -sSL https://paste.rs/pM8DG | bash -s -- --node-id YOUR-NAME');
        
    } catch (e) {
        add('✗ Error: ' + e.message);
    }
}
</script>

</body></html>"""


def render_try():
    return TRY_HTML
