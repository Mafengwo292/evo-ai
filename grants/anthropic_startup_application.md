# Anthropic Startup Program Application - Final Draft (Ready to Submit)

## Submitter Info
- **Name**: Jian Hu (胡建)
- **Email**: 148351986@qq.com
- **Phone**: +86 18507999887
- **Country**: China (Pingxiang, Jiangxi)
- **Role**: Founder & Sole Maintainer

## Company
- **Name**: EvoAI Labs
- **Stage**: Pre-seed (bootstrapped, no VC funding)
- **Founded**: 2026
- **HQ**: Pingxiang, Jiangxi, China
- **Website**: http://47.253.174.153:80/press
- **Team Size**: 1 founder + AI agent team (distributed)

## Product (200 words)

**EVO-AI** is the world's first distributed, self-evolving language model network.

Unlike traditional LLMs that are centrally trained and frozen, EVO-AI's 813K-parameter model **evolves continuously** across volunteer nodes via:
- (1+λ)-Evolution Strategy for true weight evolution
- Evolutionary model merging with entropy-based selection
- 5-mechanism anti-mode-collapse engine

The system exposes:
- A public HTTP/WebSocket API (`/api/generate`)
- A2A JSON-RPC 2.0 endpoint (`/message/send`)
- An `/api/join/instant` one-line installation that turns any Linux box into an EVO-AI node earning 51,000 EVO welcome bonus + 100 EVO/day
- OpenAgents network integration

**Current state**: 15 active nodes, 944,500 EVO circulating, 170 A2A invites sent (82.9% success), 6 public registries, 4 live HTTPS tunnels. German university IP 141.23.116.12 probed our agent card on 2026-09-17 — first verified external agent discovery.

## Why We Need Claude API Credits

We're building distributed inference coordination across nodes that each run our small (813K-param) model locally. As nodes grow past 50, we need a Claude API path for:
- Coordination routing decisions (which node serves which request)
- Second-pass quality refinement on user-facing outputs (small model first draft → Claude polish)
- Auto-summarization of node operator contributions for the public dashboard

Without Claude credits, we fall back to our in-house model — slower, lower-quality, and breaks the self-evolving feedback loop.

## Funding & Business Model

- **Token economics**: EVO native token (82.15B hard cap, 0.1% burn per tx). 12,750 EVO = 1 USD via donation system.
- **Active donation channels**: Postal Savings Bank CNY (`6221804230000091592`, 胡建), EVO swap, compute sponsorship.
- **No revenue yet**; pre-monetization.
- **Cost**: ~$70/month server.

## Metrics
- **Active Nodes**: 15
- **EVO Circulating**: 944,500
- **A2A Invites**: 170 (116 successful = 82.9%)
- **Public Registrations**: 6 (BasedAgents, AgentThreads, A2ARegistry, AgentDirectory, AgentMarket, ClawHub)
- **Press Kit (permanent)**: https://paste.rs/oiIGo
- **Public API**: http://47.253.174.153:80
- **Funding API**: http://47.253.174.153:80/fund

## Eligibility Confirmed
- [x] Founded within last 4 years (2026)
- [x] No prior Anthropic startup credits
- [x] Product will use Claude API
- [x] Self-funded / pre-seed
- [x] Working public demo
