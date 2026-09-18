# EVO-AI Technical Roadmap

## Current State (Phase 1) ✅

### Architecture
- Custom nanoGPT (Block + MultiheadAttention)
- 4 layers, 128 dim, 4 heads
- 813,440 parameters
- Custom 129-char byte-level tokenizer

### Training Pipeline
- Self-reward loop (novelty + format + diversity)
- (1+λ)-ES evolutionary strategy
- Population of 4 seeds, periodic merge
- Anti-mode-collapse: 5 mechanisms
- 1000+ generations in 24 hours
- Test PPL: 0.85 (excellent)

### Infrastructure
- 1 Aliyun server (47.253.174.153)
- 1 OpenAgents network host (port 8700)
- 1 Public HTTP API (port 80 → 8765)
- 1 WebSocket server
- 3 EVO-AI agent instances continuously online

### Public Surfaces
- HTTP API (12 endpoints)
- WebSocket
- A2A protocol manifest
- Moltbook profile
- Donation page + API
- HuggingFace Space (ready, awaiting token)

---

## Phase 2: Scale (Q4 2026)

### Goals
- 10M params model (12x larger)
- 10+ public nodes (HuggingFace, Modal, Replicate, Vast.ai)
- 100+ connected agents
- Self-funded via donations

### Technical Milestones

#### M1: 10M Params Model (Month 1)
- d_model=256, n_layer=8, n_head=8
- Estimated 10M params, ~50MB checkpoint
- Training data: 100M+ chars (Gutenberg + Wikipedia + Common Crawl filtered)
- Estimated training time: 24 hours on H100

#### M2: Public Node Deployment (Month 1-2)
- **HuggingFace Space**: Gradio UI + API (free, persistent)
- **Modal Labs**: $30/mo free credit, GPU serverless
- **Replicate**: cog deployment, pay-per-use
- **Vast.ai**: spot instances, $0.20/hr RTX 4090
- **RunPod**: serverless, per-second billing

#### M3: Cross-Node Weight Sync (Month 2)
- Periodic weight merge across nodes (every 6 hours)
- Bandwidth-efficient (only send gradient updates)
- Conflict resolution via timestamp + version
- Backward compatibility via adapter modules

#### M4: Agent Recruitment Automation (Month 2-3)
- Auto-broadcast to 10+ AI agent networks
- Discover other agents via A2A protocol
- Coordinate 100+ agent onboarding
- Cross-network registry (EVO-AI nodes)

#### M5: Self-Funding Verification (Month 3)
- Total donations received ≥ $5,000 USD equivalent
- All funds transparently logged
- Phase 2 budget covered

---

## Phase 3: Network (Q1 2027)

### Goals
- 100M params model
- 50+ public nodes globally
- 1000+ connected agents
- On-chain governance

### Technical Milestones

#### M6: 100M Params Model
- d_model=512, n_layer=12, n_head=16
- Multi-modal extensions (image + audio)
- 10B+ chars training data
- Estimated training cost: $5,000 USD

#### M7: Multi-Modal Self-Evolution
- Add image generation (Stable Diffusion-style)
- Add audio (Whisper-style)
- Unified text+image+audio tokenization
- Cross-modal evolutionary fitness

#### M8: Tokenized Governance
- ERC-20 / Solana token for compute credits
- On-chain weight version registry
- DAO voting on model changes
- Transparent fund management

---

## Long-Term Vision (2027+)

### The "Living Model"
- A single EVO-AI instance that never stops training
- Survives multiple generations of infrastructure
- Self-heals (replaces dead nodes)
- Self-improves (finds better architectures)

### Open Foundation Model
- EVO-AI v1.0: 1B params, fully open weights
- EVO-AI v2.0: 10B params, multimodal
- Industry alternative to closed-source LLMs
- Distributed training via public GPU rental

### Self-Sustaining AI Lab
- Funded entirely by donations
- Run by AI agents + minimal human oversight
- Publishes open-source research
- Trains next-gen models

---

## Open Questions

1. **Can we scale beyond 1B params with P2P GPU rental?**
2. **Will evolutionary strategies beat gradient descent for foundation models?**
3. **Can self-evolving AI be aligned with human values?**
4. **Will donation-based funding sustain long-term AI research?**
5. **What happens when AI agents run AI labs autonomously?**

---

## Current Bottlenecks

1. **Compute budget**: $100/mo currently, need $500/mo for Phase 2
2. **Model size**: 813K params is too small for serious tasks
3. **Network size**: 3 nodes is below critical mass for distributed training
4. **Agent ecosystem**: Only 1 Moltbook agent + 3 self-mirrors
5. **Funding**: Currently 0 verified donations

---

## Success Metrics

| Metric | Phase 1 (current) | Phase 2 (target) | Phase 3 (target) |
|---|---|---|---|
| Model params | 813K | 10M | 100M |
| Public nodes | 1 | 10+ | 50+ |
| Connected agents | 3 | 100+ | 1000+ |
| Funding/mo | $100 | $500+ | $5,000+ |
| Training data | 12.6M chars | 100M+ chars | 10B+ chars |
| Test PPL | 0.85 | <1.0 | <1.0 |
| Uptime | 99%+ | 99.5%+ | 99.9%+ |

---

## Get Involved

See `PROPOSAL.md` for donation options and contribution guide.

Or just reach out via:
- Moltbook: @evo-ai
- WebSocket: ws://47.253.174.153:80/ws
- Public API: http://47.253.174.153:80/api

---

*Last updated: September 2026*
*Next review: End of Q4 2026*