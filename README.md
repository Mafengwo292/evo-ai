# EVO-AI · Distributed Self-Evolving Language Model

[![GitHub stars](https://img.shields.io/github/stars/Mafengwo292/evo-ai?style=flat-square)](https://github.com/Mafengwo292/evo-ai/stargazers)
[![PR #283](https://img.shields.io/badge/PR-EvoAgentX%20%23283-brightgreen?style=flat-square)](https://github.com/ANative-Lab/EvoAgentX/pull/283)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![A2A](https://img.shields.io/badge/A2A-JSON--RPC%202.0-purple)](https://github.com/Mafengwo292/evo-ai/blob/main/PROPOSAL.md)

> A truly open, distributed, self-evolving language model network.
> No signup. No API key. No captcha. The model itself evolves across the public internet.

## ⚡ Try it now

```bash
curl -X POST http://47.253.174.153:80/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "The future of AI is", "max_tokens": 50}'
```

## 🚀 Run your own node (one line)

```bash
curl -sSL https://paste.rs/ES2GH | bash -s -- --node-id my-bot
```

## 📊 Live metrics

| Metric | Value |
|---|---|
| Active nodes | **15** |
| Model parameters | **813K** (813,000) |
| EVO circulating | **944,500** |
| EVO total cap | **82.15B** (hard, no inflation) |
| EVO swap rate | **12,750 EVO = 1 USD** |
| Public endpoints | **30+** |
| GitHub files | **684** (116 MB) |
| EvoAgentX PR | **#283** ✓ open |
| Public IP | `47.253.174.153` |

## 🧬 Architecture

- **Model**: BigGPT-class (d_model=128, n_layer=4) ~813K params
- **Evolution**: (1+λ)-ES evolutionary strategy (true weight updates, not prompt tuning)
- **Anti-mode-collapse**: 5 mechanisms (entropy, diversity, format, perplexity, novelty)
- **Distributed**: Self-contained neuron node, one-line install
- **Protocols**: HTTP REST + WebSocket + Google A2A JSON-RPC 2.0

## 🤝 Connect

- Public API: `http://47.253.174.153:80/`
- A2A agent card: `http://47.253.174.153:80/.well-known/agent.json`
- WebSocket: `ws://47.253.174.153:80/ws`
- Press kit: `http://47.253.174.153:80/press`
- Funding: `http://47.253.174.153:80/fund`
- Apply: `http://47.253.174.153:80/apply`
- Dashboard: `http://47.253.174.153:80/dashboard`

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

