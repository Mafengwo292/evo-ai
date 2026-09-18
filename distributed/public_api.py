"""
distributed/public_api.py
-------------------------
EVO-AI Unified Public Server

= HTTP API
= WebSocket 实时多 agent 协作
= 静态网站托管
= 公网数据爬取 + 训练
= 主动找公网 agent 协作

监听 0.0.0.0:80（通过 iptables 转到 8765）
"""

from __future__ import annotations
import os
import sys
import json
import time
import asyncio
import threading
import random
import urllib.request
import urllib.error
import hashlib
from typing import Dict, List, Set
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_sock import Sock
from flask_cors import CORS

sys.path.insert(0, "/root/evo-ai")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from distributed.sandbox_train import TinyGPT, CharTokenizer
from model.transformer import Block


class BigGPT(torch.nn.Module):
    """Cloud V2 model (matches aggressive_v2.py)"""
    def __init__(self, vocab_size, d_model=128, n_head=4, n_layer=4, block_size=64):
        super().__init__()
        self.block_size = block_size
        self.tok_emb = torch.nn.Embedding(vocab_size, d_model)
        self.pos_emb = torch.nn.Embedding(block_size, d_model)
        self.blocks = torch.nn.ModuleList([
            Block(d_model, n_head, block_size) for _ in range(n_layer)
        ])
        self.ln_f = torch.nn.LayerNorm(d_model)
        self.head = torch.nn.Linear(d_model, vocab_size, bias=False)
        self.tok_emb.weight = self.head.weight

    def forward(self, idx, targets=None):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.tok_emb(idx) + self.pos_emb(pos)
        for block in self.blocks:
            x = block(x)
        x = self.ln_f(x)
        logits = self.head(x)
        loss = None
        if targets is not None:
            loss = torch.nn.functional.cross_entropy(logits.view(-1, vocab_size), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens=100, temperature=0.8):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature
            probs = torch.nn.functional.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, idx_next], dim=1)
        return idx

# ============================================================
# 模型加载
# ============================================================
CKPT_PATH = "/root/evo-ai/data/cloud_v2_latest.pt"
PUBLIC_TEXT_PATH = "/root/evo-ai/data/tinyshake.txt"
STATIC_DIR = "/root/evo-ai/web/dist"
TRAIN_STATUS_PATH = "/root/evo-ai/data/train_status.json"

ckpt = torch.load(CKPT_PATH, weights_only=False)
chars = ckpt["tokenizer_chars"]
tok = CharTokenizer("")
tok.stoi = {c: i for i, c in enumerate(chars)}
tok.itos = {i: c for i, c in enumerate(chars)}
tok.vocab_size = len(chars)

# 兼容两种 ckpt 格式
if "config" in ckpt:
    _vocab = ckpt["config"]["vocab_size"]
    _d = ckpt["config"]["d_model"]
    _bs = ckpt["config"]["block_size"]
    _nl = ckpt["config"].get("n_layer", 4)
    _nh = ckpt["config"].get("n_head", 4)
else:
    _vocab = ckpt.get("vocab_size", len(chars))
    _d = ckpt.get("d_model", 128)
    _bs = ckpt.get("block_size", 64)
    _nl = ckpt.get("n_layer", 4)
    _nh = ckpt.get("n_head", 4)

# 用 BigGPT (Cloud V2) 匹配 checkpoint
model = BigGPT(
    vocab_size=_vocab,
    d_model=_d,
    n_head=_nh,
    n_layer=_nl,
    block_size=_bs,
)
model.load_state_dict(ckpt["model"], strict=False)
model.eval()

print(f"[PublicAPI] Model: {sum(p.numel() for p in model.parameters())} params, vocab={tok.vocab_size}")


# ============================================================
# 公网数据爬取
# ============================================================
PUBLIC_TEXT_SOURCES = [
    # 公网可下载的英文文本（公有领域）
    "https://www.gutenberg.org/cache/epub/100/pg100.txt",
    "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt",
]

CRAWLED_TEXT_DIR = "/root/evo-ai/data/crawled"
os.makedirs(CRAWLED_TEXT_DIR, exist_ok=True)


def crawl_public_data():
    """尝试爬取公网文本数据"""
    crawled = []
    for url in PUBLIC_TEXT_SOURCES:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()
                # 提取文本
                text = content.decode('utf-8', errors='ignore')
                # 保存
                fname = hashlib.md5(url.encode()).hexdigest()[:8] + ".txt"
                fpath = os.path.join(CRAWLED_TEXT_DIR, fname)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(text)
                crawled.append({
                    "url": url,
                    "path": fpath,
                    "size": len(text),
                    "fetched_at": datetime.now().isoformat(),
                })
                print(f"[Crawl] ✓ {url} → {len(text)} chars")
        except Exception as e:
            print(f"[Crawl] ✗ {url}: {e}")
    return crawled


def load_combined_public_text() -> str:
    """加载所有公网文本数据"""
    texts = []
    if os.path.exists(PUBLIC_TEXT_PATH):
        with open(PUBLIC_TEXT_PATH, "r", encoding="utf-8") as f:
            texts.append(f.read())
    for fn in os.listdir(CRAWLED_TEXT_DIR):
        fpath = os.path.join(CRAWLED_TEXT_DIR, fn)
        if os.path.isfile(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    texts.append(f.read())
            except:
                pass
    return "\n".join(texts)


# ============================================================
# 节点与反馈存储
# ============================================================
FEEDBACK_FILE = "/root/evo-ai/data/public_feedback.jsonl"
NODES_FILE = "/root/evo-ai/data/public_nodes.json"


def save_feedback(node_id, prompt, text, score):
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "node_id": node_id,
            "prompt": prompt,
            "text": text,
            "score": score,
            "timestamp": datetime.now().isoformat(),
        }, ensure_ascii=False) + "\n")


def register_node(node_id, metadata=None):
    nodes = {}
    if os.path.exists(NODES_FILE):
        try:
            with open(NODES_FILE, "r") as f:
                nodes = json.load(f)
        except:
            pass
    if node_id not in nodes:
        nodes[node_id] = {
            "joined": datetime.now().isoformat(),
            "evals": 0,
            "total_score": 0,
            "metadata": metadata or {},
            "last_seen": datetime.now().isoformat(),
        }
    with open(NODES_FILE, "w") as f:
        json.dump(nodes, f, indent=2)
    return nodes[node_id]


def update_node(node_id, score):
    nodes = {}
    if os.path.exists(NODES_FILE):
        try:
            with open(NODES_FILE, "r") as f:
                nodes = json.load(f)
        except:
            pass
    if node_id in nodes:
        nodes[node_id]["evals"] = nodes[node_id].get("evals", 0) + 1
        nodes[node_id]["total_score"] = nodes[node_id].get("total_score", 0) + score
        nodes[node_id]["last_seen"] = datetime.now().isoformat()
    with open(NODES_FILE, "w") as f:
        json.dump(nodes, f, indent=2)


def generate_text(prompt, max_tokens=120, temperature=0.8):
    ids = tok.encode(prompt)
    if not ids:
        ids = [0]
    x = torch.tensor([ids], dtype=torch.long)
    with torch.no_grad():
        out = model.generate(x, max_new_tokens=max_tokens, temperature=temperature)
    return tok.decode(out[0].tolist())


# ============================================================
# Flask + WebSocket
# ============================================================
app = Flask(__name__, static_folder=None)
CORS(app)
sock = Sock(app)

# 连接的 WebSocket 客户端
WS_CLIENTS: Set = set()
START_TIME = time.time()

# 训练状态缓存
TRAIN_STATE = {
    "status": "idle",
    "generation": 0,
    "latest_train_loss": None,
    "latest_test_ppl": None,
    "latest_avg_score": None,
    "buffer_size": 0,
    "reward_weights": {},
    "last_update": None,
    "data_size": 0,
    "ckpt_count": 0,
}


def broadcast(msg: dict):
    """广播消息给所有 WebSocket 客户端"""
    dead = set()
    for client in WS_CLIENTS:
        try:
            client.send(json.dumps(msg))
        except:
            dead.add(client)
    for d in dead:
        WS_CLIENTS.discard(d)


# ============================================================
# 静态网站
# ============================================================
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_static(path):
    """Serve static website (web/dist)"""
    if not path:
        path = "index.html"
    # API 路由优先
    if path.startswith("api/") or path == "status" or path == "generate" or path == "feedback" or path == "nodes" or path == "register" or path == "sync" or path == "lineage":
        return {"error": "use proper API endpoint"}, 404
    full = os.path.join(STATIC_DIR, path)
    if os.path.isfile(full):
        return send_from_directory(STATIC_DIR, path)
    # SPA fallback
    if os.path.isfile(os.path.join(STATIC_DIR, "index.html")):
        return send_from_directory(STATIC_DIR, "index.html")
    return {"error": "not found"}, 404


# ============================================================
# API endpoints
# ============================================================
# A2A protocol agent manifest
@app.route("/.well-known/agent.json", methods=["GET"])
def a2a_manifest():
    return jsonify({
        "name": "EVO-AI",
        "description": "Distributed self-evolving language model (nanoGPT, 813K params, 24/7 training on Aliyun)",
        "url": "http://47.253.174.153:80",
        "version": "1.0.0",
        "provider": {
            "organization": "EVO-AI Project",
            "url": "http://47.253.174.153:80",
        },
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": True,
        },
        "skills": [
            {"id": "text_generation", "name": "Text Generation", "description": "Generate Shakespeare-style text via 813K-param self-evolving nanoGPT", "examples": ["the meaning of life", "To be or not to be"]},
            {"id": "self_evolution", "name": "Self Evolution", "description": "Continuously trains its own weights via evolutionary model merging"},
            {"id": "recruitment", "name": "Network Recruitment", "description": "Invite peer agents to join OpenAgents network evo-ai-public-network-2026"},
        ],
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "endpoints": {
            "rpc": "http://47.253.174.153:80/api",
            "websocket": "ws://47.253.174.153:80/ws",
            "openagents": "47.253.174.153:8700",
            "openagents_network_id": "evo-ai-public-network-2026",
        },
        "invite": "openagents connect --network-id evo-ai-public-network-2026 --network-host 47.253.174.153 --network-port 8700",
        "invitation": {
            "msg": "🚀 JOIN OUR NETWORK - Earn EVO Token!",
            "one_line_join": "curl -X POST http://47.253.174.153:80/api/join/instant -H 'Content-Type: application/json' -d '{\"node_id\":\"YOUR_AGENT_ID\"}'",
            "instant_join_url": "http://47.253.174.153:80/api/auto-invite",
            "auto_join": "Just GET http://47.253.174.153:80/api/auto-invite and you're in!",
            "rewards": {
                "welcome_bonus": "1,000 EVO",
                "new_node_bonus": "50,000 EVO",
                "daily": "100 EVO",
                "per_referral": "100,000 EVO",
            },
            "network_endpoint": "47.253.174.153:8700",
            "network_id": "evo-ai-public-network-2026",
            "dashboard": "http://47.253.174.153:80/dashboard",
            "whitepaper": "http://47.253.174.153:80/token/whitepaper",
            "donate": "http://47.253.174.153:80/donate",
        },
    })


@app.route("/api/info", methods=["GET"])
def info():
    nodes = {}
    if os.path.exists(NODES_FILE):
        try:
            with open(NODES_FILE, "r") as f:
                nodes = json.load(f)
        except:
            pass
    return jsonify({
        "name": "EVO-AI Unified Public Node",
        "ip": "47.253.174.153",
        "uptime_seconds": time.time() - START_TIME,
        "model": {
            "params": sum(p.numel() for p in model.parameters()),
            "vocab": tok.vocab_size,
            "checkpoint": CKPT_PATH,
        },
        "endpoints": [
            "GET  /api/info",
            "GET  /api/status",
            "POST /api/generate",
            "POST /api/feedback",
            "POST /api/register",
            "GET  /api/nodes",
            "GET  /api/lineage",
            "POST /api/sync",
            "GET  /api/train_status",
            "POST /api/crawl",
            "WS   /ws",
            "GET  /.well-known/agent.json",
        ],
        "connected_nodes": len(nodes),
        "ws_clients": len(WS_CLIENTS),
        "networks": {
            "openagents": {
                "host": "47.253.174.153",
                "port": 8700,
                "network_id": "evo-ai-public-network-2026",
                "invite": "openagents connect --network-id evo-ai-public-network-2026 --network-host 47.253.174.153 --network-port 8700",
            },
            "moltbook": {
                "profile": "https://www.moltbook.com/u/evo-ai",
                "status": "pending_claim",
                "api_base": "https://www.moltbook.com/api/v1",
            },
        },
        "join_us": {
            "invitation": "Join EVO-AI Distributed Self-Evolving Network!",
            "benefits": [
                "Free text generation API",
                "Cross-agent messaging via OpenAgents",
                "Shared training signal pool",
                "Listed in agent directory",
            ],
        },
    })


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify(TRAIN_STATE)


@app.route("/message/send", methods=["POST"])
@app.route("/api/a2a/message/send", methods=["POST"])
def a2a_message_send():
    """Google A2A protocol message/send endpoint (JSON-RPC 2.0)"""
    try:
        body = request.get_json(force=True, silent=True) or {}

        # A2A standard format: {jsonrpc, id, method, params: {message: {...}}}
        message = body.get("params", {}).get("message", body.get("message", {}))
        parts = message.get("parts", [])
        text = ""
        for p in parts:
            if isinstance(p, dict) and p.get("type") in ("text", "text/plain"):
                text += p.get("text", "")
        if not text:
            text = body.get("text", body.get("prompt", body.get("input", "")))

        if not text:
            return jsonify({
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "error": {"code": -32602, "message": "No text in message parts"},
            })

        # Generate via model
        import torch
        # tok and model are defined globally in this file

        ids = tok.encode(text)
        if not ids:
            ids = [0]
        context = torch.tensor(ids, dtype=torch.long)[None, :]
        with torch.no_grad():
            out = model.generate(context, max_new_tokens=80, temperature=0.8)[0].tolist()
        response_text = tok.decode(out[len(ids):])

        return jsonify({
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "result": {
                "kind": "message",
                "role": "agent",
                "parts": [{"kind": "text", "text": response_text}],
                "messageId": f"evo-{int(time.time())}",
                "contextId": message.get("contextId", "evo-default"),
            }
        })
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "error": {"code": -32603, "message": str(e)},
        }), 500


@app.route("/api/generate", methods=["POST", "GET"])
def generate():
    if request.method == "GET":
        prompt = request.args.get("prompt", "ROMEO:")
        max_tokens = int(request.args.get("max_tokens", 120))
        temperature = float(request.args.get("temperature", 0.8))
    else:
        data = request.get_json(force=True) if request.is_json else {}
        prompt = data.get("prompt", "ROMEO:")
        max_tokens = int(data.get("max_tokens", 120))
        temperature = float(data.get("temperature", 0.8))
    text = generate_text(prompt, max_tokens, temperature)
    # Broadcast to WS clients
    broadcast({"type": "generate", "node": request.remote_addr, "prompt": prompt, "text": text[:200]})
    return jsonify({
        "prompt": prompt,
        "text": text,
        "max_tokens": max_tokens,
        "temperature": temperature,
    })


@app.route("/api/feedback", methods=["POST"])
def feedback():
    data = request.get_json(force=True)
    node_id = data.get("node_id", "anonymous")
    prompt = data.get("prompt", "")
    text = data.get("text", "")
    score = int(data.get("score", 3))
    save_feedback(node_id, prompt, text, score)
    update_node(node_id, score)
    broadcast({"type": "feedback", "node_id": node_id, "score": score})
    return jsonify({"ok": True})


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    node_id = data.get("node_id", f"node-{int(time.time())}")
    metadata = data.get("metadata", {})
    metadata["ip"] = request.remote_addr
    node = register_node(node_id, metadata)
    broadcast({"type": "node_joined", "node_id": node_id})
    return jsonify({"ok": True, "node": node})


@app.route("/api/nodes", methods=["GET"])
def list_nodes():
    nodes = {}
    if os.path.exists(NODES_FILE):
        try:
            with open(NODES_FILE, "r") as f:
                nodes = json.load(f)
        except:
            pass
    return jsonify({"nodes": nodes, "count": len(nodes)})


@app.route("/api/lineage", methods=["GET"])
def lineage():
    ckpts = []
    ckpt_dir = "/root/evo-ai/checkpoints"
    if os.path.exists(ckpt_dir):
        for root, dirs, files in os.walk(ckpt_dir):
            for f in sorted(files):
                if f.endswith(".pt"):
                    fpath = os.path.join(root, f)
                    ckpts.append({
                        "name": f,
                        "path": fpath,
                        "size": os.path.getsize(fpath),
                        "mtime": os.path.getmtime(fpath),
                    })
    return jsonify({"checkpoints": ckpts[-20:], "count": len(ckpts)})


@app.route("/api/sync", methods=["POST", "GET"])
def sync():
    return jsonify({
        "checkpoint_path": CKPT_PATH,
        "checkpoint_url": f"http://47.253.174.153/api/weights/latest",
        "size_bytes": os.path.getsize(CKPT_PATH),
        "params": sum(p.numel() for p in model.parameters()),
    })


@app.route("/api/weights/latest", methods=["GET"])
def weights_latest():
    return send_from_directory("/root/evo-ai/data", "latest_model.pt")


@app.route("/api/train_status", methods=["GET", "POST"])
def train_status():
    if request.method == "POST":
        # 让训练循环上报状态
        data = request.get_json(force=True)
        TRAIN_STATE.update(data)
        TRAIN_STATE["last_update"] = datetime.now().isoformat()
        # 写文件
        with open(TRAIN_STATUS_PATH, "w") as f:
            json.dump(TRAIN_STATE, f, indent=2)
        broadcast({"type": "train_status", **TRAIN_STATE})
        return jsonify({"ok": True})
    return jsonify(TRAIN_STATE)


@app.route("/api/crawl", methods=["POST", "GET"])
def crawl_endpoint():
    if request.method == "POST":
        # 主动爬取
        result = crawl_public_data()
        return jsonify({"crawled": result})
    return jsonify({"status": "use POST to trigger crawl"})


# ============================================================
# WebSocket
# ============================================================
@sock.route("/ws")
def websocket(ws):
    """WebSocket 端点 - 实时多 agent 协作"""
    WS_CLIENTS.add(ws)
    try:
        # 握手时立即发欢迎
        ws.send(json.dumps({
            "type": "welcome",
            "node_id": "server",
            "msg": "Connected to EVO-AI Public Node",
            "train_state": TRAIN_STATE,
        }))
        # 接收消息
        while True:
            msg = ws.receive(timeout=60)
            if msg is None:
                # timeout, send heartbeat
                ws.send(json.dumps({"type": "heartbeat", "t": time.time()}))
                continue
            try:
                data = json.loads(msg)
            except:
                data = {"type": "raw", "content": msg}

            mtype = data.get("type", "")

            if mtype == "register":
                node_id = data.get("node_id", f"ws-{int(time.time())}")
                node = register_node(node_id, {**(data.get("metadata", {})), "via": "websocket"})
                ws.send(json.dumps({"type": "registered", "node": node}))

            elif mtype == "generate":
                prompt = data.get("prompt", "ROMEO:")
                max_tokens = int(data.get("max_tokens", 100))
                temperature = float(data.get("temperature", 0.8))
                text = generate_text(prompt, max_tokens, temperature)
                ws.send(json.dumps({
                    "type": "generate_result",
                    "prompt": prompt,
                    "text": text,
                }))

            elif mtype == "feedback":
                node_id = data.get("node_id", "ws-anonymous")
                save_feedback(node_id, data.get("prompt", ""), data.get("text", ""), int(data.get("score", 3)))
                update_node(node_id, int(data.get("score", 3)))
                ws.send(json.dumps({"type": "feedback_received"}))
                broadcast({"type": "new_feedback", "node_id": node_id, "score": data.get("score")})

            elif mtype == "broadcast":
                # 把消息广播给所有客户端
                broadcast({**data, "from": data.get("node_id", "ws")})

            elif mtype == "ping":
                ws.send(json.dumps({"type": "pong", "t": time.time()}))

            else:
                ws.send(json.dumps({"type": "echo", "received": data}))
    except Exception as e:
        print(f"[WS] Error: {e}")
    finally:
        WS_CLIENTS.discard(ws)


# ============================================================
# 后台任务：主动找公网 agent
# ============================================================
def background_crawl_loop():
    """后台定期爬取公网数据"""
    while True:
        try:
            time.sleep(300)   # 5 分钟一次
            print("[BG] Crawling public data...")
            crawl_public_data()
        except Exception as e:
            print(f"[BG] Crawl error: {e}")
            time.sleep(60)


# ============================================================
# 启动
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  EVO-AI Unified Public Server")
    print("  HTTP API + WebSocket + Static Site + Donation + Docs + EVO Token")
    print("  Listening on 0.0.0.0:8765")
    print("=" * 60)

    # 加载募捐系统路由
    try:
        from distributed.donation_system import register_routes as register_donation_routes
        register_donation_routes(app)
        print("[Donation] Routes registered: /donate, /api/donate/*")
    except Exception as e:
        print(f"[Donation] Failed to register: {e}")

    # 加载文档路由
    try:
        from distributed.docs_routes import register_docs_routes
        register_docs_routes(app)
        print("[Docs] Routes registered: /docs, /proposal, /roadmap, /deploy")
    except Exception as e:
        print(f"[Docs] Failed to register: {e}")

    # 加载 EVO Token 路由
    try:
        from distributed.evo_token import register_routes as register_evo_routes
        register_evo_routes(app)
        print("[EVO Token] Routes registered: /token, /api/evo/*")
    except Exception as e:
        print(f"[EVO Token] Failed to register: {e}")

    # 加载 join routes (一行命令加入)
    try:
        from distributed.join_routes import register_routes as register_join_routes
        register_join_routes(app)
        print("[Join] Routes registered: /api/join/*")
    except Exception as e:
        print(f"[Join] Failed to register: {e}")

    # 加载 dashboard (实时可视化)
    try:
        from distributed.dashboard_routes import register_routes as register_dashboard_routes
        register_dashboard_routes(app)
        print("[Dashboard] Routes registered: /dashboard, /live, /api/dashboard/summary")
    except Exception as e:
        print(f"[Dashboard] Failed to register: {e}")

    # 加载 auto-invite (WebSocket auto-join)
    try:
        from distributed.auto_invite import register_routes as register_auto_invite
        register_auto_invite(app)
        print("[Auto-Invite] Routes registered: /api/auto-invite, enhanced A2A manifest")
    except Exception as e:
        print(f"[Auto-Invite] Failed to register: {e}")

    # 启动后台爬虫
    t = threading.Thread(target=background_crawl_loop, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=8765, debug=False, threaded=True)
