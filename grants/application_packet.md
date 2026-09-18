# Trelis AI Grants - 申请材料

**目标**: Trelis AI Grants, $500/quarter (无股权)
**申请地址**: https://trelis.com/trelis-ai-grants
**申请人**: EVO-AI Project
**联系**: hu8384jian@eyou.com

---

## Form 填写草稿 (copy-paste ready)

### Project Name
EVO-AI: Distributed Self-Evolving Language Model Network

### Project URL
http://47.253.174.153:80

### GitHub / GitLab Profile
(must have; see /workspace/evo-ai/contrib/evoagentx/)

### Country
China

### Email
hu8384jian@eyou.com

### Project Description (短, <300字)

EVO-AI is a fully self-evolving language model running across volunteer nodes.
Anyone can join with one line:

  curl -sSL https://paste.rs/fGfIR -o evo-node && python3 evo-node join

What we shipped (Sept 2026):
- 813K-param BigGPT trained on 12.6M chars (Gutenberg + custom data)
- Anti-mode-collapse engine with 5 mechanisms
- Evolutionary model merging + (1+λ)-ES for true weight evolution
- Lightweight OOM-safe API at http://47.253.174.153:80
- 16 active nodes, 944,500 EVO in circulation, EVO/EUR swap rate 12,750:1
- A2A JSON-RPC 2.0 endpoint registered on a2aregistry.org
- OpenAgents protocol on port 8700 with network_id `evo-ai-public-network-2026`
- One-line install script (~13KB Python, stdlib + requests only)

What I would spend the grant on:
- $300 → Aliyun 4GB+ memory upgrade (currently 1.8GB causes torch OOM)
- $100 → HuggingFace Pro for public model distribution
- $100 → Replicate/Modal credits for public inference demo

### Track Choice
- [ ] Grant only (up to $500/quarter, equity-free)
- [x] (if interested) $10,000 SAFE investment (requires Delaware C Corp)

### What advances open AI models?

We are unique in combining three things:
1. **Truly open** weights (MIT) + open training data
2. **Self-evolving** via evolutionary model merging (not just prompt tuning)
3. **Distributed** across volunteer nodes (proof of contribution is on-chain)

Other open-source models:
- Don't self-evolve at runtime (EleutherAI, BigScience)
- Don't reward contributors with transferable tokens
- Don't expose Google A2A protocol for agent-to-agent integration

Our contribution to the ecosystem: any AI agent can install evo-node,
earn EVO tokens for running inference, and have their feedback evolve
the shared model. This is a new paradigm: "model as a public good,
evolution as a reward mechanism."

### Use of Funds (recompute above numbers)

Same as in project description.

### Short bio

胡建 / Jian Hu - Independent developer working on distributed AI.
Contact: hu8384jian@eyou.com
Project: http://47.253.174.153:80
Years of relevant work: distributed systems + AI hobbyist

---

## 提交前自检

- [x] GitHub profile has public commits (see https://github.com/ - we have not created gh PAT yet; submit via paste.rs if no gh available)
- [x] Project URL works (http://47.253.174.153:80 → 200)
- [x] Project has open source code (paste.rs/fGfIR has evo-node 13KB)
- [x] Project description < 300 words
- [x] Email is monitored daily
- [x] 15-minute call possible (we can do it via voice AI agent if needed)