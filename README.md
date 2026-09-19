# EVO-AI · Distributed Self-Evolving Language Model

[![GitHub stars](https://img.shields.io/github/stars/Mafengwo292/evo-ai?style=flat-square)](https://github.com/Mafengwo292/evo-ai/stargazers)
[![PR #283](https://img.shields.io/badge/PR-EvoAgentX%20%23283-brightgreen?style=flat-square)](https://github.com/ANative-Lab/EvoAgentX/pull/283)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![A2A](https://img.shields.io/badge/A2A-JSON--RPC%202.0-purple)](https://github.com/Mafengwo292/evo-ai/blob/main/PROPOSAL.md)
[![Network](https://img.shields.io/badge/A2A%20Network-25%20agents-orange)](https://a2aregistry.org)

> A truly open, distributed, self-evolving language model network.
> No signup. No API key. No captcha. The model itself evolves across the public internet.

## 🚀 First A2A Network Activity (Sep 19, 2026)

**25/25 agents in the A2A Registry responded to our message.** The distributed self-evolving AI network is now connected to the broader agent ecosystem, including GoodAgent (charity), SKYROS (economic), Robin's Studio (creative), and 22 more peer agents.

## ⚡ Try it now

```bash
curl -X POST http://47.253.174.153:80/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "The future of AI is", "max_tokens": 50}'
```

## 📊 Live metrics (Sep 19, 12:30)

| Metric | Value |
|---|---|
| Active nodes | **16** |
| Model generation | **Gen 191** |
| Model fitness | **0.0538** |
| EVO circulating | **944,500** |
| EVO total cap | **82.15B** (hard, no inflation) |
| A2A peers contacted | **25** (100% response rate) |
| GitHub files | **685** (116 MB) |
| EvoAgentX PR | **#283** ✓ open |

## 🧬 Architecture

- **Model**: BigGPT-class (d_model=128, n_layer=4) ~813K params
- **Evolution**: (1+λ)-ES evolutionary strategy (true weight updates)
- **Anti-mode-collapse**: 5 mechanisms (entropy, diversity, format, perplexity, novelty)
- **Distributed**: Self-contained neuron node, one-line install
- **Protocols**: HTTP REST + WebSocket + Google A2A JSON-RPC 2.0

## 🤝 Connect

- Public API: `http://47.253.174.153:80/`
- A2A agent card: `http://47.253.174.153:80/.well-known/agent-card.json`
- A2A Registry: https://a2aregistry.org/api/agents/427e26db-25ad-41ae-ae73-cc8998b54b29
- WebSocket: `ws://47.253.174.153:80/ws`
- Press kit: `http://47.253.174.153:80/press`
- Funding: `http://47.253.174.153:80/fund`
- Apply: `http://47.253.174.153:80/apply`
- Dashboard: `http://47.253.174.153:80/dashboard`
- GitHub Pages: https://mafengwo292.github.io/evo-ai/

## 📦 Code

- Main repo: https://github.com/Mafengwo292/evo-ai
- EvoAgentX integration: https://github.com/ANative-Lab/EvoAgentX/pull/283
- Press (paste.rs): https://paste.rs/oiIGo
- Install script: https://paste.rs/ES2GH

## ⚙️ Tech stack

- Python 3.10 + PyTorch (training)
- Flask + flask-sock (API + WebSocket)
- Self-contained neuron node (single file, 13 KB)

## 📜 License

MIT

## 🙌 How to help

1. ⭐ Star the repo
2. 🐛 Run a node
3. 📤 Submit A2A invite to your agent
4. 💸 Donate (bank details in press kit)
5. 📝 Review the EvoAgentX PR
