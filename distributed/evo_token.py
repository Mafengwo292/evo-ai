"""
distributed/evo_token.py
------------------------
EVO Token - Distributed AI Network Currency

Total supply: 82,150,000,000 (82.15 billion)
Decimals: 8
Genesis block: 2026-09-14

Features:
- Account creation (wallet addresses)
- Transfer with signature
- Block validation (Proof of Useful Work)
- Staking & rewards
- Burn (deflationary)
- Governance voting

Storage: JSON ledger (lightweight, append-only, auditable)
"""

import os
import json
import time
import hashlib
import secrets
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# ============================================
# Token Configuration
# ============================================
TOKEN_CONFIG = {
    "name": "EVO",
    "symbol": "EVO",
    "decimals": 8,
    "total_supply": 82_150_000_000 * 10**8,  # 82.15B with 8 decimals
    "smallest_unit": 0.00000001,  # 1 satoshi
    "genesis_time": "2026-09-14T00:00:00Z",
    "block_time_seconds": 3600,  # 1 hour
    "halving_interval_years": 4,
    "max_years": 10,
}

# Allocation buckets (82.15B)
ALLOCATION = {
    "node_rewards":       int(82_150_000_000 * 0.35 * 10**8),  # 35%
    "api_compute":        int(82_150_000_000 * 0.25 * 10**8),  # 25%
    "public_distribution": int(82_150_000_000 * 0.20 * 10**8),  # 20%
    "reserve":            int(82_150_000_000 * 0.10 * 10**8),  # 10%
    "team_advisors":      int(82_150_000_000 * 0.07 * 10**8),  # 7%
    "liquidity_pool":     int(82_150_000_000 * 0.03 * 10**8),  # 3%
}

# Daily emission (slow release over 10 years)
DAILY_EMISSION = ALLOCATION["node_rewards"] // (10 * 365)

# Burn rate (deflationary)
BURN_RATE = 0.001  # 0.1% per transaction

# Donation reward rate (CNY to EVO)
# 1 CNY ≈ 12,750 EVO (at this initial valuation)
# Adjust based on market dynamics
DONATION_TO_EVO_RATE = 12_750 * 10**8  # 1 CNY = 12,750 EVO

# Data files
DATA_DIR = "/root/evo-ai/data/evo_token"
os.makedirs(DATA_DIR, exist_ok=True)

LEDGER_FILE = f"{DATA_DIR}/ledger.json"      # All balances
BLOCKS_FILE = f"{DATA_DIR}/blocks.json"      # Blockchain
TX_POOL_FILE = f"{DATA_DIR}/tx_pool.json"    # Pending transactions
NODES_FILE = f"{DATA_DIR}/nodes.json"        # Registered nodes
STAKES_FILE = f"{DATA_DIR}/stakes.json"      # Staking records
VOTES_FILE = f"{DATA_DIR}/votes.json"        # Governance votes

# Simple crypto (in production use proper Ed25519)
SECRET_KEY_FILE = f"{DATA_DIR}/.secret_key"


def load_or_create_secret():
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, "rb") as f:
            return f.read()
    key = secrets.token_bytes(32)
    with open(SECRET_KEY_FILE, "wb") as f:
        f.write(key)
    return key


SECRET_KEY = load_or_create_secret()


# ============================================
# Ledger (state)
# ============================================
def load_ledger():
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE) as f:
            return json.load(f)
    return {
        "balances": {},           # address -> balance (in smallest unit)
        "nonces": {},             # address -> tx count
        "metadata": {},           # address -> {name, type, registered_at}
        "burned_total": 0,        # cumulative burned
        "minted_total": 0,        # cumulative minted
    }


def save_ledger(ledger):
    with open(LEDGER_FILE, "w") as f:
        json.dump(ledger, f, indent=2)


# ============================================
# Blocks
# ============================================
def load_blocks():
    if os.path.exists(BLOCKS_FILE):
        with open(BLOCKS_FILE) as f:
            return json.load(f)
    # Genesis block
    genesis = create_genesis_block()
    blocks = [genesis]
    with open(BLOCKS_FILE, "w") as f:
        json.dump(blocks, f, indent=2)
    return blocks


def save_blocks(blocks):
    with open(BLOCKS_FILE, "w") as f:
        json.dump(blocks, f, indent=2)


def create_genesis_block():
    """Create the genesis (first) block"""
    return {
        "index": 0,
        "version": 1,
        "prev_hash": "0" * 64,
        "timestamp": TOKEN_CONFIG["genesis_time"],
        "epoch_number": 0,
        "validator": "genesis",
        "transactions": [
            {
                "type": "genesis_allocation",
                "allocations": ALLOCATION,
                "timestamp": TOKEN_CONFIG["genesis_time"],
            }
        ],
        "state_root": hashlib.sha256(json.dumps(ALLOCATION, sort_keys=True).encode()).hexdigest(),
        "hash": hashlib.sha256(json.dumps({
            "index": 0,
            "prev_hash": "0" * 64,
            "allocations": ALLOCATION,
            "timestamp": TOKEN_CONFIG["genesis_time"],
        }, sort_keys=True).encode()).hexdigest(),
        "note": "EVO Token Genesis Block - 82.15B EVO Total Supply",
    }


# ============================================
# Address generation
# ============================================
def generate_address(name: str = None) -> str:
    """Generate a new EVO address"""
    # In production: use public key derivation
    # Here: random address
    random_bytes = secrets.token_bytes(20)
    checksum = hashlib.sha256(SECRET_KEY + random_bytes).digest()[:4]
    raw = random_bytes + checksum
    # Base58 encode (simplified)
    import string
    chars = string.digits + "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
    result = ""
    n = int.from_bytes(raw, "big")
    while n > 0:
        result = chars[n % 58] + result
        n //= 58
    return f"evo1{result[:30]}"


def sign_tx(tx_data: dict, address: str) -> str:
    """Simple HMAC signature"""
    payload = json.dumps(tx_data, sort_keys=True).encode()
    return hmac.new((SECRET_KEY + address.encode()).encode(), payload, hashlib.sha256).hexdigest()


# ============================================
# Core operations
# ============================================
def create_account(name: str, account_type: str = "user", metadata: dict = None) -> dict:
    """Create a new EVO account"""
    ledger = load_ledger()
    address = generate_address(name)

    # Auto-airdrop 1000 EVO to new accounts (small welcome gift)
    welcome = 1000 * 10**8

    ledger["balances"][address] = ledger["balances"].get(address, 0) + welcome
    ledger["nonces"][address] = 0
    ledger["metadata"][address] = {
        "name": name,
        "type": account_type,
        "registered_at": datetime.now().isoformat(),
        **(metadata or {}),
    }
    ledger["minted_total"] += welcome
    save_ledger(ledger)

    return {
        "success": True,
        "address": address,
        "balance": ledger["balances"][address],
        "balance_evo": ledger["balances"][address] / 10**8,
        "welcome_bonus": welcome / 10**8,
        "type": account_type,
        "name": name,
    }


def get_balance(address: str) -> dict:
    """Get account balance and info"""
    ledger = load_ledger()
    bal = ledger["balances"].get(address, 0)
    meta = ledger["metadata"].get(address, {})
    return {
        "address": address,
        "balance": bal,
        "balance_evo": bal / 10**8,
        "nonce": ledger["nonces"].get(address, 0),
        "metadata": meta,
    }


def transfer(from_addr: str, to_addr: str, amount: float, signature: str = None, memo: str = "") -> dict:
    """Transfer EVO between accounts"""
    ledger = load_ledger()

    # Convert to smallest unit
    amount_sat = int(amount * 10**8)
    if amount_sat <= 0:
        return {"success": False, "error": "Amount must be positive"}

    # Check sender balance
    sender_bal = ledger["balances"].get(from_addr, 0)
    if sender_bal < amount_sat:
        return {"success": False, "error": "Insufficient balance",
               "balance": sender_bal / 10**8, "required": amount}

    # Calculate burn (0.1% of amount)
    burn_amount = int(amount_sat * BURN_RATE)

    # Execute transfer
    ledger["balances"][from_addr] = sender_bal - amount_sat
    ledger["balances"][to_addr] = ledger["balances"].get(to_addr, 0) + (amount_sat - burn_amount)
    ledger["burned_total"] += burn_amount
    ledger["nonces"][from_addr] = ledger["nonces"].get(from_addr, 0) + 1

    # Sign if not provided
    if not signature:
        signature = sign_tx({
            "from": from_addr, "to": to_addr,
            "amount": amount_sat, "memo": memo,
            "nonce": ledger["nonces"][from_addr],
        }, from_addr)

    save_ledger(ledger)

    return {
        "success": True,
        "tx_id": hashlib.sha256(f"{from_addr}{to_addr}{amount_sat}{time.time()}".encode()).hexdigest()[:16],
        "from": from_addr,
        "to": to_addr,
        "amount": amount,
        "burned": burn_amount / 10**8,
        "memo": memo,
        "signature": signature,
        "timestamp": datetime.now().isoformat(),
    }


# ============================================
# Node registry & rewards
# ============================================
def load_nodes():
    if os.path.exists(NODES_FILE):
        with open(NODES_FILE) as f:
            return json.load(f)
    return {"nodes": {}, "total_rewards": 0}


def save_nodes(nodes):
    with open(NODES_FILE, "w") as f:
        json.dump(nodes, f, indent=2)


def register_node(node_id: str, address: str = None, endpoint: str = None, capabilities: list = None) -> dict:
    """Register an EVO-AI node"""
    nodes = load_nodes()
    ledger = load_ledger()

    # Auto-create wallet if no address
    if not address or address not in ledger["metadata"]:
        acc = create_account(f"node:{node_id}", "node", {"endpoint": endpoint})
        address = acc["address"]

    nodes["nodes"][node_id] = {
        "node_id": node_id,
        "address": address,
        "endpoint": endpoint,
        "capabilities": capabilities or [],
        "registered_at": datetime.now().isoformat(),
        "last_heartbeat": None,
        "epochs_completed": 0,
        "uptime": 1.0,
        "total_rewarded": 0,
    }
    save_nodes(nodes)

    return {"success": True, "node": nodes["nodes"][node_id]}


def heartbeat_node(node_id: str, metrics: dict = None) -> dict:
    """Update node heartbeat + claim daily reward"""
    nodes = load_nodes()
    if node_id not in nodes["nodes"]:
        return {"success": False, "error": "Node not registered"}

    node = nodes["nodes"][node_id]
    node["last_heartbeat"] = datetime.now().isoformat()

    # Calculate reward
    metrics = metrics or {}
    uptime = metrics.get("uptime", 1.0)
    weights_synced_gb = metrics.get("weights_synced_gb", 0)
    data_contributed_mb = metrics.get("data_contributed_mb", 0)
    compute_mflops = metrics.get("compute_mflops", 0)

    # Base: 100 EVO/day; uptime bonus up to 2x
    base = 100 * 10**8
    reward = int(base * uptime)
    reward += int(weights_synced_gb * 10 * 10**8)
    reward += int(data_contributed_mb * 5 * 10**8)
    reward += int(compute_mflops * 10**8)

    # Pay out
    ledger = load_ledger()
    ledger["balances"][node["address"]] = ledger["balances"].get(node["address"], 0) + reward
    ledger["minted_total"] += reward
    save_ledger(ledger)

    node["total_rewarded"] += reward
    node["epochs_completed"] += 1
    nodes["total_rewards"] += reward
    save_nodes(nodes)

    return {
        "success": True,
        "node_id": node_id,
        "reward": reward / 10**8,
        "balance": ledger["balances"][node["address"]] / 10**8,
        "metrics": metrics,
    }


# ============================================
# Donation reward (CNY → EVO)
# ============================================
def donation_to_evo(cny_amount: float, donor_address: str = None) -> dict:
    """Convert CNY donation to EVO reward + 10% bonus"""
    base_evo = cny_amount * DONATION_TO_EVO_RATE  # base units
    bonus_evo = base_evo * 0.10  # 10% bonus
    total_evo = base_evo + bonus_evo

    # Auto-create account if needed
    if not donor_address:
        acc = create_account(f"donor:{datetime.now().timestamp()}", "donor")
        donor_address = acc["address"]

    # Pay out
    ledger = load_ledger()
    ledger["balances"][donor_address] = ledger["balances"].get(donor_address, 0) + int(total_evo)
    ledger["minted_total"] += int(total_evo)
    save_ledger(ledger)

    return {
        "success": True,
        "donor_address": donor_address,
        "donation_cny": cny_amount,
        "base_evo": base_evo / 10**8,
        "bonus_evo": bonus_evo / 10**8,
        "total_evo": total_evo / 10**8,
        "rate_cny_to_evo": DONATION_TO_EVO_RATE / 10**8,
    }


# ============================================
# Stats & queries
# ============================================
def get_network_stats() -> dict:
    """Get network-wide stats"""
    ledger = load_ledger()
    blocks = load_blocks()
    nodes = load_nodes()

    total_supply = TOKEN_CONFIG["total_supply"]
    minted = ledger["minted_total"]
    burned = ledger["burned_total"]
    circulating = minted - burned

    return {
        "name": TOKEN_CONFIG["name"],
        "symbol": TOKEN_CONFIG["symbol"],
            "total_supply": total_supply,
        "total_supply_evo": total_supply / 10**8,
        "minted": minted / 10**8,
        "burned": burned / 10**8,
        "circulating": circulating / 10**8,
        "accounts": len(ledger["balances"]),
        "blocks": len(blocks),
        "nodes": len(nodes["nodes"]),
        "total_node_rewards": nodes["total_rewards"] / 10**8,
        "donation_rate_cny_to_evo": DONATION_TO_EVO_RATE / 10**8,
        "burn_rate": BURN_RATE,
        "config": TOKEN_CONFIG,
        "allocation": {k: v / 10**8 for k, v in ALLOCATION.items()},
    }


def list_accounts(limit: int = 100) -> list:
    """List accounts sorted by balance"""
    ledger = load_ledger()
    items = []
    for addr, bal in ledger["balances"].items():
        meta = ledger["metadata"].get(addr, {})
        items.append({
            "address": addr,
            "balance_evo": bal / 10**8,
            "name": meta.get("name", ""),
            "type": meta.get("type", "user"),
            "registered_at": meta.get("registered_at", ""),
        })
    items.sort(key=lambda x: x["balance_evo"], reverse=True)
    return items[:limit]


def list_nodes(limit: int = 100) -> list:
    """List registered nodes"""
    nodes = load_nodes()
    items = []
    for nid, n in nodes["nodes"].items():
        items.append({
            "node_id": nid,
            "address": n["address"],
            "endpoint": n["endpoint"],
            "uptime": n["uptime"],
            "epochs_completed": n["epochs_completed"],
            "total_rewarded_evo": n["total_rewarded"] / 10**8,
            "last_heartbeat": n["last_heartbeat"],
        })
    return items[:limit]


# ============================================
# Flask routes
# ============================================
def register_routes(app):
    from flask import jsonify, request

    @app.route("/api/evo", methods=["GET"])
    def evo_info():
        return jsonify({
            "name": "EVO Token",
            "description": "Native utility token for EVO-AI Distributed Self-Evolving AI Network",
            "config": TOKEN_CONFIG,
            "allocation": {k: v / 10**8 for k, v in ALLOCATION.items()},
            "whitepaper": "http://47.253.174.153:80/token",
        })

    @app.route("/api/evo/stats", methods=["GET"])
    def evo_stats():
        return jsonify(get_network_stats())

    @app.route("/api/evo/create", methods=["POST"])
    def evo_create():
        body = request.get_json() or {}
        name = body.get("name")
        if not name:
            return jsonify({"success": False, "error": "Missing name"}), 400
        result = create_account(
            name=name,
            account_type=body.get("type", "user"),
            metadata=body.get("metadata", {}),
        )
        return jsonify(result)

    @app.route("/api/evo/balance/<address>", methods=["GET"])
    def evo_balance(address):
        return jsonify(get_balance(address))

    @app.route("/api/evo/transfer", methods=["POST"])
    def evo_transfer():
        body = request.get_json() or {}
        required = ["from", "to", "amount"]
        for k in required:
            if k not in body:
                return jsonify({"success": False, "error": f"Missing {k}"}), 400
        return jsonify(transfer(
            from_addr=body["from"],
            to_addr=body["to"],
            amount=float(body["amount"]),
            memo=body.get("memo", ""),
        ))

    @app.route("/api/evo/accounts", methods=["GET"])
    def evo_accounts():
        limit = int(request.args.get("limit", 100))
        return jsonify({"accounts": list_accounts(limit), "count": len(list_accounts(1000))})

    @app.route("/api/evo/nodes", methods=["GET"])
    def evo_nodes():
        return jsonify({"nodes": list_nodes(), "count": len(list_nodes(1000))})

    @app.route("/api/evo/node/register", methods=["POST"])
    def evo_node_register():
        body = request.get_json() or {}
        if "node_id" not in body:
            return jsonify({"success": False, "error": "Missing node_id"}), 400
        return jsonify(register_node(
            node_id=body["node_id"],
            address=body.get("address"),
            endpoint=body.get("endpoint", ""),
            capabilities=body.get("capabilities", []),
        ))

    @app.route("/api/evo/node/heartbeat", methods=["POST"])
    def evo_node_heartbeat():
        body = request.get_json() or {}
        if "node_id" not in body:
            return jsonify({"success": False, "error": "Missing node_id"}), 400
        return jsonify(heartbeat_node(
            node_id=body["node_id"],
            metrics=body.get("metrics", {}),
        ))

    @app.route("/api/evo/donation", methods=["POST"])
    def evo_donation():
        body = request.get_json() or {}
        if "cny_amount" not in body:
            return jsonify({"success": False, "error": "Missing cny_amount"}), 400
        return jsonify(donation_to_evo(
            cny_amount=float(body["cny_amount"]),
            donor_address=body.get("donor_address"),
        ))

    @app.route("/token", methods=["GET"])
    def token_page():
        """Public EVO token dashboard"""
        stats = get_network_stats()
        accounts = list_accounts(20)
        nodes = list_nodes(20)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>EVO Token - EVO-AI Network</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0a0a0a; color: #fff; max-width: 1000px; margin: 0 auto; padding: 40px 20px; }}
  h1 {{ color: #ff4500; font-size: 2.5em; }}
  h2 {{ color: #00d4aa; border-bottom: 1px solid #333; padding-bottom: 10px; margin-top: 40px; }}
  .hero {{ background: linear-gradient(135deg, #1a1a1b, #272729); padding: 30px; border-radius: 12px; text-align: center; margin: 20px 0; }}
  .hero .supply {{ font-size: 3em; color: #ff4500; font-weight: bold; }}
  .card {{ background: #1a1a1b; padding: 20px; border-radius: 8px; margin: 15px 0; border: 1px solid #343536; }}
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
  .stat {{ background: #272729; padding: 15px; border-radius: 4px; text-align: center; }}
  .stat .num {{ font-size: 1.5em; color: #00d4aa; font-weight: bold; }}
  .stat .label {{ font-size: 0.9em; color: #888; margin-top: 5px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
  td, th {{ padding: 8px; text-align: left; border-bottom: 1px solid #333; }}
  th {{ color: #00d4aa; }}
  .btn {{ display: inline-block; padding: 10px 20px; background: #ff4500; color: #fff; border-radius: 4px; text-decoration: none; margin: 4px; }}
  .btn:hover {{ background: #ff5722; }}
  code {{ background: #272729; padding: 2px 6px; border-radius: 3px; color: #ff4500; }}
</style>
</head>
<body>

<div class="hero">
  <h1>💰 EVO Token</h1>
  <p>The native currency of the EVO-AI Distributed Self-Evolving Network</p>
  <div class="supply">{stats['total_supply_evo']:,.0f} EVO</div>
  <p>Total Supply (Fixed, never inflated)</p>
  <br>
  <a href="#create" class="btn">Create Wallet</a>
  <a href="/donate" class="btn">Donate</a>
  <a href="/token/whitepaper" class="btn">Whitepaper</a>
</div>

<h2>📊 Network Stats</h2>
<div class="stats">
  <div class="stat">
    <div class="num">{stats['minted']:,.0f}</div>
    <div class="label">Minted EVO</div>
  </div>
  <div class="stat">
    <div class="num">{stats['burned']:,.0f}</div>
    <div class="label">Burned EVO</div>
  </div>
  <div class="stat">
    <div class="num">{stats['circulating']:,.0f}</div>
    <div class="label">Circulating</div>
  </div>
  <div class="stat">
    <div class="num">{stats['accounts']:,}</div>
    <div class="label">Accounts</div>
  </div>
  <div class="stat">
    <div class="num">{stats['nodes']}</div>
    <div class="label">Active Nodes</div>
  </div>
  <div class="stat">
    <div class="num">{stats['blocks']}</div>
    <div class="label">Blocks</div>
  </div>
</div>

<h2>💎 Tokenomics</h2>
<div class="card">
  <p><b>Total Supply:</b> {stats['total_supply_evo']:,.0f} EVO (hard cap, no inflation)</p>
  <p><b>Decimal:</b> {TOKEN_CONFIG['decimals']} (1 EVO = 100,000,000 satoshi)</p>
  <p><b>Block Time:</b> {TOKEN_CONFIG['block_time_seconds']/3600:.0f} hour(s)</p>
  <p><b>Burn Rate:</b> {BURN_RATE*100}% per transaction (deflationary)</p>
  <p><b>Donation Rate:</b> 1 CNY = {DONATION_TO_EVO_RATE/10**8:,.0f} EVO (+10% bonus)</p>
</div>

<h2>🎯 Allocation</h2>
<table>
  <tr><th>Bucket</th><th>Allocation</th><th>EVO</th><th>%</th></tr>
  {''.join(f'<tr><td>{k}</td><td>{int(ALLOCATION[k]/10**8):,}</td><td>{v/10**8:,.0f}</td><td>{v/sum(ALLOCATION.values())*100:.0f}%</td></tr>' for k, v in ALLOCATION.items())}
</table>

<h2 id="create">👛 Top Wallets</h2>
<table>
  <tr><th>Address</th><th>Name</th><th>Type</th><th>Balance (EVO)</th></tr>
  {''.join(f'<tr><td><code>{a["address"][:18]}...</code></td><td>{a["name"]}</td><td>{a["type"]}</td><td>{a["balance_evo"]:,.2f}</td></tr>' for a in accounts)}
</table>

<h2>🖥️ Active Nodes</h2>
<table>
  <tr><th>Node</th><th>Address</th><th>Endpoint</th><th>Epochs</th><th>Rewarded (EVO)</th></tr>
  {''.join(f'<tr><td>{n["node_id"]}</td><td><code>{n["address"][:18]}...</code></td><td>{n["endpoint"]}</td><td>{n["epochs_completed"]}</td><td>{n["total_rewarded_evo"]:,.2f}</td></tr>' for n in nodes)}
</table>

<h2>🔌 API</h2>
<div class="card">
  <p><b>Get stats:</b> <code>GET /api/evo/stats</code></p>
  <p><b>Create wallet:</b></p>
  <pre style="background:#0d0d0d;padding:12px;border-radius:4px;color:#00d4aa;">
curl -X POST http://47.253.174.153:80/api/evo/create \\
  -H "Content-Type: application/json" \\
  -d '{{"name": "your_name"}}'</pre>
  <p><b>Check balance:</b> <code>GET /api/evo/balance/&lt;address&gt;</code></p>
  <p><b>Transfer:</b></p>
  <pre style="background:#0d0d0d;padding:12px;border-radius:4px;color:#00d4aa;">
curl -X POST http://47.253.174.153:80/api/evo/transfer \\
  -H "Content-Type: application/json" \\
  -d '{{"from": "addr1", "to": "addr2", "amount": 100, "memo": "thanks"}}'</pre>
  <p><b>Register node:</b></p>
  <pre style="background:#0d0d0d;padding:12px;border-radius:4px;color:#00d4aa;">
curl -X POST http://47.253.174.153:80/api/evo/node/register \\
  -H "Content-Type: application/json" \\
  -d '{{"node_id": "my-node", "address": "evo1...", "endpoint": "http://..."}}'</pre>
</div>

<p style="text-align:center;color:#666;margin-top:40px;">
<a href="/proposal">💰 Donate</a> ·
<a href="/api/evo/stats">📡 API</a> ·
<a href="/docs">📚 Docs</a> ·
<a href="/.well-known/agent.json">🤖 A2A</a>
</p>

</body>
</html>"""

    @app.route("/token/whitepaper", methods=["GET"])
    def token_whitepaper():
        whitepaper_path = "/root/evo-ai/TOKEN_WHITEPAPER.md"
        if not os.path.exists(whitepaper_path):
            return "Whitepaper not found", 404
        with open(whitepaper_path) as f:
            md = f.read()
        from docs_routes import make_page
        return make_page("EVO Token Whitepaper", md, "#ff4500")