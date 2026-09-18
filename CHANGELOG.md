# Changelog

All notable changes to EVO-AI are documented here.

## [0.5.0] - 2026-09-18

### Added
- 🚀 **GitHub repo live**: https://github.com/Mafengwo292/evo-ai (684 files, 116 MB)
- 🔀 **EvoAgentX PR #283**: https://github.com/ANative-Lab/EvoAgentX/pull/283 (EvoAILLM backend integration)
- 🌐 **GitHub Pages site**: https://mafengwo292.github.io/evo-ai/
- 🏷️ **Repo topics**: llm, distributed, evolution, ai-agents, self-evolving, a2a, openagents
- 📝 **Issues #1-2**: Welcome + Help Wanted (Run a node)
- 🔑 **Classic PAT** with admin:enterprise + repo + workflow + 19 scopes
- 🐛 **GitHub monitor cron** (*/30 min) — auto-responds to PR comments, watches for stars

### Tunnel infrastructure
- ✅ **Pinggy tunnel**: `https://kthjm-47-253-174-153.run.pinggy-free.link` (60-min rotation)
- ✅ **Serveo tunnel**: `https://9fabb1cfe16ebf33-47-253-174-153.serveousercontent.com`
- ✅ **Direct IP**: `http://47.253.174.153:80` (iptables 80→8765)
- ✅ **iptables restored** after server restart

### Live API stats
- 15 nodes (3 internal + 12 test/curl)
- 944,500 EVO circulating
- 944M EVO minted
- 21 systemd + cron jobs active

## [0.4.0] - 2026-09-17

### Added
- ⭐ State management system (`/root/evo-ai/state/`)
- 🤖 13 new persistent cron jobs (lightweight_evo, continuous_evolution, expand_a2a_v2, etc.)
- 🔒 self_drive_safe with fcntl lock + memory gate
- 📡 systemd services: evo-api, evo-pub, evo-test (all auto-restart)

### Performance
- Generation 11 / fitness 0.0092 (5 gens/hour)
- Training data: 13.5 KB (Wikipedia/Arxiv/GitHub)
- 5 anti-mode-collapse mechanisms active

## [0.3.0] - 2026-09-14

### Added
- 🌐 Public HTTP API on 47.253.174.153:80
- 🤝 A2A JSON-RPC 2.0 protocol
- 📦 13KB self-contained neuron node (one-line install)
- 🪙 EVO Token (82.15B hard cap, 0.1% burn)
- 📋 Public press kit + funding API
- 💸 Donation system (4 tiers)

## [0.2.0] - 2026-09-08

### Added
- (1+λ)-ES evolutionary strategy
- BigGPT 813K-param base model
- Aliyun training pipeline (v4 fix)

## [0.1.0] - 2026-09-01

### Added
- Initial nanoGPT-based architecture
- Distributed scheduler skeleton
- Anti-mode-collapse engine
