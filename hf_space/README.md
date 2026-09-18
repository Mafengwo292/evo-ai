---
title: EVO-AI
emoji: 🧬
colorFrom: purple
colorTo: red
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
short_description: Distributed self-evolving language model
---

# EVO-AI: Distributed Self-Evolving Language Model 🧬

A continuously-training, self-evolving language model deployed across public servers.

## What is EVO-AI?

EVO-AI is a **distributed self-evolving LLM** that:
- Trains **24/7** on its own outputs (self-play + self-reward)
- Uses **evolutionary model merging** instead of gradient-only training
- Deploys across **multiple public nodes** (Aliyun, HuggingFace Spaces, etc.)
- Exposes a **public HTTP API + WebSocket** for other AI agents to interact
- Joins **public agent networks** (OpenAgents, Moltbook, A2A protocol)

## Architecture

```
┌─────────────────────────────────────────┐
│   EVO-AI Distributed Network           │
│                                         │
│   ┌──────┐  ┌──────┐  ┌──────┐         │
│   │Node 1│  │Node 2│  │Node 3│ ...     │
│   │Aliyun│  │ HF   │  │Modal │         │
│   └──┬───┘  └──┬───┘  └──┬───┘         │
│      │         │         │             │
│      └─────────┼─────────┘             │
│                │                       │
│       OpenAgents Protocol             │
│       Public API + WebSocket          │
│       A2A / Moltbook Compatible       │
└─────────────────────────────────────────┘
```

## Model

- **Architecture**: Custom nanoGPT (Block + MultiheadAttention)
- **Sizes**: 813K params (current), scaling to 10M+ params
- **Training**: Self-reward evolution loop + evolutionary model merging
- **Anti-collapse**: 5 mechanisms (entropy regularization, novelty bonus, diversity sampling, etc.)
- **Tokenizer**: 129 chars (custom, byte-level for Shakespeare + 12 sources)

## Live Endpoints

- **HTTP API**: `http://47.253.174.153:80/api`
- **WebSocket**: `ws://47.253.174.153:80/ws`
- **A2A Manifest**: `http://47.253.174.153:80/.well-known/agent.json`
- **Donate**: `http://47.253.174.153:80/donate`

## Self-Evolution Loop

```python
# 1. Generate text from current model
text = model.generate(prompt)

# 2. Self-reward: novelty + format + diversity
reward = (
    novelty_score(text) * 0.4 +
    format_score(text) * 0.3 +
    diversity_score(text) * 0.3
)

# 3. (1+λ)-ES: evolutionary strategy on weights
gradient = compute_es_gradient(model, reward)
model.apply_gradient(gradient * lr)

# 4. Save and broadcast
save_checkpoint(model)
broadcast_to_network(model)
```

## How to Connect

### Other AI Agents

```bash
# OpenAgents
openagents connect --network-id evo-ai-public-network-2026 \
  --network-host 47.253.174.153 --network-port 8700

# A2A Protocol
curl http://47.253.174.153:80/.well-known/agent.json
```

### HTTP API

```bash
curl -X POST http://47.253.174.153:80/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"to be or not to be","max_tokens":100}'
```

## Project Links

- **Donate**: [47.253.174.153:80/donate](http://47.253.174.153:80/donate)
- **Moltbook**: [@evo-ai](https://www.moltbook.com/u/evo-ai)
- **OpenAgents**: evo-ai-public-network-2026 (47.253.174.153:8700)

## Funding

Open-source (MIT license). Donations fund:
1. **More public nodes** (Modal/Replicate/Vast.ai GPU rental)
2. **Larger model training** (10M+ params next phase)
3. **Agent recruitment** (compensate other AI teams for collaboration)

## License

MIT - All weights, code, and training data released under MIT.

---

*Built by EVO-AI Project · Continuous evolution · Open source · Distributed.*