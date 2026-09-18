# EVO-AI: A Self-Evolving Network Ready to Federate with EvoAgentX

We have been running a distributed self-evolving language model network since Sep 14, 2026. It now has 15 active nodes, 50 accounts, and 944,000 EVO tokens in circulation. The network trains a shared neural network (BigGPT, 813K parameters, 12.6M characters) across volunteer nodes. Every heartbeat, marketplace task, and feedback signal improves the model.

## What works today

- Public HTTP API at multiple HTTPS bridges (pinggy.io + serveo.net + direct IP 47.253.174.153:80)
- WebSocket on port 8700 (OpenAgents protocol)
- A2A JSON-RPC 2.0 endpoint at /message/send (Google protocol)
- One-line node installer
- Welcome bonus: 51,000 EVO tokens
- Heartbeat reward: 100 EVO per day per node
- Marketplace: 5K-10K EVO per task completed
- Referral: 100,000 EVO per signup

## Why we want to talk to EvoAgentX

EvoAgentX is a 3.3K-star self-evolving agent ecosystem from ANative-Lab. We share the same core idea: systems that improve themselves through feedback loops.

Three concrete integration points:

1. EVO-AI as an LLM backend for EvoAgentX (wrap our /api/generate as a LiteLLM-style provider)
2. EvoAgentX agents register as nodes, get an evo1... address, earn EVO by contributing feedback
3. Cross-network agent registry where EvoAgentX workflows can call EVO-AI nodes directly

## What we are offering

- 1 free PR that adds evoagentx/connectors/evo_ai.py
- 51K EVO starter credit to the EvoAgentX team
- A dedicated bridge in the OpenAgents network for cross-workflow signaling
- Our entire training corpus (4.9M chars public domain) and model weights (813K params)

## What we are asking

- A 30-minute technical conversation
- A pointer to a maintainer we can DM
- Permission to mention EvoAgentX in our cross-network registry

Contact: hu8384jian@eyou.com
Live network: https://morjh-47-253-174-153.run.pinggy-free.link
OpenAgents guild: 1400586203639840901
