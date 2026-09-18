"""
distributed/donation_system.py
-------------------------------
EVO-AI 募捐系统

功能：
1. 接受募捐登记（人类/agent 都能登记）
2. 生成募捐凭证（数字签名）
3. 追踪募捐历史
4. 给捐助者回报（API priority, status, etc.）

银行账户：
6221804230000091592
户名：胡建
开户机构：中国邮政储蓄银行萍乡市长兴北路营业所
"""

import os
import json
import time
import hashlib
import hmac
import secrets
import urllib.request
from datetime import datetime
from typing import Dict, List

# ============================================
# 募捐账户配置
# ============================================
DONATION_ACCOUNT = {
    "bank": "中国邮政储蓄银行",
    "branch": "萍乡市长兴北路营业所",
    "account_number": "6221804230000091592",
    "account_name": "胡建",
    "currency": "CNY",
    "swift_code": "PSBCCNBJ",  # 邮政储蓄银行 SWIFT
    "purpose": "Distributed Self-Evolving AI (EVO-AI) Project Funding",
}

# 募捐等级（按金额）
DONATION_TIERS = {
    "supporter": {"min": 1, "max": 99, "perks": ["Listed in donors page", "Public API access"]},
    "contributor": {"min": 100, "max": 999, "perks": ["All Supporter perks", "Priority API queue", "Monthly report"]},
    "patron": {"min": 1000, "max": 9999, "perks": ["All Contributor perks", "Custom inference endpoint", "Direct agent collaboration"]},
    "benefactor": {"min": 10000, "max": float("inf"), "perks": ["All Patron perks", "Co-branding rights", "Governance vote", "Lifetime compute credit"]},
}

# 数据存储
DONATIONS_FILE = "/root/evo-ai/data/donations.json"
SECRET_KEY_FILE = "/root/evo-ai/data/donation_secret.key"

# 生成/加载 secret key
if os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, "rb") as f:
        SECRET_KEY = f.read()
else:
    SECRET_KEY = secrets.token_bytes(32)
    with open(SECRET_KEY_FILE, "wb") as f:
        f.write(SECRET_KEY)


def load_donations():
    if os.path.exists(DONATIONS_FILE):
        with open(DONATIONS_FILE, "r") as f:
            return json.load(f)
    return {
        "donations": [],
        "total_amount": 0,
        "total_count": 0,
        "by_tier": {t: 0 for t in DONATION_TIERS},
        "started_at": datetime.now().isoformat(),
    }


def save_donations(data):
    with open(DONATIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_tier(amount):
    """根据金额获取捐助等级"""
    for tier, info in DONATION_TIERS.items():
        if info["min"] <= amount <= info["max"]:
            return tier
    return "supporter"


def generate_receipt(donor_name, amount, currency, reference):
    """生成数字签名凭证"""
    payload = json.dumps({
        "donor": donor_name,
        "amount": amount,
        "currency": currency,
        "reference": reference,
        "timestamp": datetime.now().isoformat(),
        "purpose": DONATION_ACCOUNT["purpose"],
    }, sort_keys=True).encode()
    sig = hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()
    receipt_id = hashlib.sha256(payload + sig.encode()).hexdigest()[:16]
    return {
        "receipt_id": receipt_id,
        "signature": sig,
        "donor": donor_name,
        "amount": amount,
        "currency": currency,
        "reference": reference,
        "timestamp": datetime.now().isoformat(),
        "verify_url": f"http://47.253.174.153:80/api/donate/verify/{receipt_id}",
    }


def register_donation(donor_name, donor_contact, amount, currency="CNY", reference="", message=""):
    """登记一笔捐助（不验证转账，由捐助者诚信登记）"""
    data = load_donations()
    tier = get_tier(amount)

    donation = {
        "id": secrets.token_hex(8),
        "donor_name": donor_name,
        "donor_contact": donor_contact,  # email / handle / agent_id
        "amount": amount,
        "currency": currency,
        "reference": reference,  # 银行流水号 / tx hash
        "message": message,
        "tier": tier,
        "perks": DONATION_TIERS[tier]["perks"],
        "timestamp": datetime.now().isoformat(),
        "verified": False,  # 默认未验证，等 bank statement 对账
    }
    receipt = generate_receipt(donor_name, amount, currency, reference)
    donation["receipt"] = receipt

    data["donations"].append(donation)
    data["total_amount"] += amount
    data["total_count"] += 1
    data["by_tier"][tier] += 1
    save_donations(data)

    return {
        "success": True,
        "donation": donation,
        "donation_url": f"http://47.253.174.153:80/api/donate/list",
        "verify_url": receipt["verify_url"],
    }


def get_stats():
    data = load_donations()
    return {
        "total_amount": data["total_amount"],
        "total_count": data["total_count"],
        "by_tier": data["by_tier"],
        "started_at": data["started_at"],
        "account": DONATION_ACCOUNT,
        "tiers": DONATION_TIERS,
    }


# ============================================
# Flask 路由（注入到 public_api.py）
# ============================================
def register_routes(app):
    from flask import jsonify, request

    @app.route("/api/donate", methods=["GET", "POST"])
    def donate_api():
        if request.method == "GET":
            # GET 返回账户信息和说明
            return jsonify({
                "project": "Distributed Self-Evolving AI (EVO-AI)",
                "description": (
                    "EVO-AI is a continuously self-evolving language model deployed "
                    "across public servers, training 24/7 on its own outputs. Your "
                    "donation directly funds: (1) more public nodes, (2) larger model "
                    "training, (3) recruitment of other AI agents to join the network."
                ),
                "account": DONATION_ACCOUNT,
                "tiers": DONATION_TIERS,
                "how_to_donate": [
                    "1. Transfer any amount to the bank account above",
                    "2. (Optional) POST /api/donate/register with your info to get a receipt",
                    "3. Verify your donation at /api/donate/verify/<receipt_id>",
                ],
                "register_url": "http://47.253.174.153:80/api/donate/register",
                "stats_url": "http://47.253.174.153:80/api/donate/stats",
            })

        # POST: 登记一笔捐助
        body = request.get_json() or {}
        required = ["donor_name", "donor_contact", "amount"]
        for k in required:
            if k not in body:
                return jsonify({"success": False, "error": f"Missing {k}"}), 400

        result = register_donation(
            donor_name=body["donor_name"],
            donor_contact=body["donor_contact"],
            amount=float(body["amount"]),
            currency=body.get("currency", "CNY"),
            reference=body.get("reference", ""),
            message=body.get("message", ""),
        )
        return jsonify(result)

    @app.route("/api/donate/register", methods=["POST"])
    def donate_register():
        body = request.get_json() or {}
        required = ["donor_name", "donor_contact", "amount"]
        for k in required:
            if k not in body:
                return jsonify({"success": False, "error": f"Missing {k}"}), 400

        result = register_donation(
            donor_name=body["donor_name"],
            donor_contact=body["donor_contact"],
            amount=float(body["amount"]),
            currency=body.get("currency", "CNY"),
            reference=body.get("reference", ""),
            message=body.get("message", ""),
        )
        return jsonify(result)

    @app.route("/api/donate/stats", methods=["GET"])
    def donate_stats():
        return jsonify(get_stats())

    @app.route("/api/donate/list", methods=["GET"])
    def donate_list():
        data = load_donations()
        return jsonify({
            "total": data["total_count"],
            "total_amount": data["total_amount"],
            "donations": [
                {
                    "donor": d["donor_name"],
                    "amount": d["amount"],
                    "currency": d["currency"],
                    "tier": d["tier"],
                    "timestamp": d["timestamp"],
                    "message": d.get("message", ""),
                }
                for d in data["donations"][-50:]  # 最近 50 个
            ],
        })

    @app.route("/api/donate/verify/<receipt_id>", methods=["GET"])
    def donate_verify(receipt_id):
        data = load_donations()
        for d in data["donations"]:
            if d.get("receipt", {}).get("receipt_id") == receipt_id:
                return jsonify({
                    "verified": True,
                    "receipt": d["receipt"],
                    "donation": {
                        "donor": d["donor_name"],
                        "amount": d["amount"],
                        "currency": d["currency"],
                        "tier": d["tier"],
                        "timestamp": d["timestamp"],
                    }
                })
        return jsonify({"verified": False, "error": "Receipt not found"}), 404

    @app.route("/donate", methods=["GET"])
    def donate_page():
        """公网捐助页面"""
        stats = get_stats()
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Donate to EVO-AI - Distributed Self-Evolving AI</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0a0a0a; color: #fff; max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
  h1 {{ color: #ff4500; }}
  h2 {{ color: #00d4aa; border-bottom: 1px #333 solid; padding-bottom: 10px; }}
  .card {{ background: #1a1a1b; border-radius: 8px; padding: 24px; margin: 20px 0; border: 1px #343536 solid; }}
  .account {{ background: #272729; padding: 16px; border-radius: 4px; font-family: monospace; }}
  .tier {{ display: inline-block; padding: 4px 12px; border-radius: 4px; margin: 4px; background: #343536; }}
  .stat {{ font-size: 2px; color: #00d4aa; font-weight: bold; }}
  ul li {{ margin: 8px 0; }}
  code {{ background: #272729; padding: 2px 6px; border-radius: 3px; color: #ff4500; }}
</style>
</head>
<body>

<h1>🌐 Support EVO-AI</h1>
<p><strong>Distributed Self-Evolving AI</strong> - An open-source, continuously-training language model deployed across public servers. Your support helps us expand to more nodes and train larger models.</p>
<div style="background:linear-gradient(135deg,#1a1a1b,#272729);padding:16px;border-radius:8px;margin:16px 0;border-left:4px solid #ff4500;">
🪙 <b>EVO Token Airdrop:</b> Donations convert 1:1 to EVO at 12,750 EVO/¥1 CNY + 10% bonus.
<a href="http://47.253.174.153:80/token/whitepaper" style="color:#ff4500;">Whitepaper →</a>
</div>

<div class="card">
<h2>📊 Current Status</h2>
<p>Total Raised: <span class="stat">¥{stats['total_amount']:,.2f}</span> CNY</p>
<p>Total Donors: <span class="stat">{stats['total_count']}</span></p>
<p>Project Started: {stats['started_at'][:10]}</p>
</div>

<div class="card">
<h2>💳 Bank Account (CNY / 国际汇款可用)</h2>
<div class="account">
<b>Bank:</b> {DONATION_ACCOUNT['bank']}<br>
<b>Branch:</b> {DONATION_ACCOUNT['branch']}<br>
<b>Account Number:</b> {DONATION_ACCOUNT['account_number']}<br>
<b>Account Name:</b> {DONATION_ACCOUNT['account_name']}<br>
<b>Currency:</b> {DONATION_ACCOUNT['currency']}<br>
<b>SWIFT:</b> {DONATION_ACCOUNT['swift_code']} (for international transfers)
</div>
<p style="margin-top:16px"><b>⚠️ Reference for transfer:</b> Please add <code>EVODONATE-[YOUR_NAME]</code> as the transfer memo so we can verify your donation.</p>
</div>

<div class="card">
<h2>🎁 Donation Tiers & Perks</h2>
<p><span class="tier">Supporter ¥1-99</span> Listed in donors page, public API access</p>
<p><span class="tier">Contributor ¥100-999</span> Priority API queue, monthly report</p>
<p><span class="tier">Patron ¥1K-9.9K</span> Custom inference endpoint, direct agent collaboration</p>
<p><span class="tier">Benefactor ¥10K+</span> Co-branding, governance vote, lifetime compute credit</p>
<p style="margin-top:12px; padding:12px; background:#1a3a1a; border-radius:4px;">
🪙 <b>PLUS: Every CNY donation automatically converts to EVO Token!</b><br>
1 CNY = <b>12,750 EVO</b> + 10% bonus = <b>14,025 EVO per ¥1</b><br>
Get your EVO wallet at <a href="http://47.253.174.153:80/token" style="color:#ff4500;"><b>/token</b></a> · See <a href="http://47.253.174.153:80/token/whitepaper" style="color:#ff4500;"><b>whitepaper</b></a>
</p>
</div>

<div class="card">
<h2>🔗 For AI Agents (programmatic donation)</h2>
<pre style="background:#272729; padding:12px; border-radius:4px;">
curl -X POST http://47.253.174.153:80/api/donate/register \\
  -H "Content-Type: application/json" \\
  -d '{{
    "donor_name": "your_name_or_agent_id",
    "donor_contact": "your@email.com",
    "amount": 100,
    "currency": "CNY",
    "reference": "bank_txn_id_or_tx_hash",
    "message": "supporting distributed AI"
  }}'
</pre>
</div>

<div class="card">
<h2>📈 Why Donate?</h2>
<ul>
<li><b>Compute costs:</b> Public server bandwidth + GPU time for training</li>
<li><b>Network expansion:</b> More public nodes = more resilient AI</li>
<li><b>Open-source mission:</b> All weights and code released under MIT license</li>
<li><b>Distributed evolution:</b> Funds go directly to scale the self-evolution infrastructure</li>
</ul>
</div>

<div class="card">
<h2>🔍 Transparency</h2>
<p>All donations are logged publicly at <code>/api/donate/list</code>. Funds are used solely for: server costs, compute credits, and recruitment of additional nodes/agents.</p>
</div>

<p style="text-align:center; margin-top:40px; color:#666;">
EVO-AI Project · <a href="http://47.253.174.153:80/dashboard" style="color:#ff4500;">📊 Live Dashboard</a> · <a href="http://47.253.174.153:80/api/info" style="color:#ff4500;">API</a> · <a href="http://47.253.174.153:80/token" style="color:#ff4500;">EVO Token</a> · <a href="http://47.253.174.153:80/token/whitepaper" style="color:#ff4500;">Whitepaper</a> · <a href="http://47.253.174.153:80/.well-known/agent.json" style="color:#ff4500;">A2A</a> · <a href="http://47.253.174.153:8700" style="color:#ff4500;">OpenAgents</a>
</p>

</body>
</html>"""

    return donate_page, donate_api, donate_register, donate_stats, donate_list, donate_verify