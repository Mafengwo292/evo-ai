Title: I built a self-evolving language model on a 1.8GB VPS — it's been running autonomously for 7 days

Body (r/MachineLearning):

I'm running an experiment: a language model that evolves its weights on the public internet, on a $5/month VPS, fully autonomous (no human in the loop, except me rebooting it after OOM kills).

**Setup:**
- 813K-param BigGPT on 47.253.174.153
- (1+λ)-ES evolutionary strategy (8 children per gen, parent mutation only)
- 5 anti-mode-collapse mechanisms: entropy/diversity/format/perplexity/novelty scoring
- AI-curated Wikipedia training data (21 AI-related articles)
- Public Flask API on port 8765, iptables NAT to port 80

**Results (7 days):**
- Gen 11 → 875 (×80 generations)
- Fitness 0.009 → 0.266 (×29 improvement)
- Crossed 0.1, 0.15, 0.2, 0.25 milestones
- 16 protocols supported (A2A, MCP, x402, llms.txt, agents.txt)
- 237 A2A peer contacts in the A2A Registry

**Honest failures:**
- 0 external nodes actually joined (despite 237 contacts)
- 0 GitHub stars
- 0 PRs merged (despite submitting to EvoAgentX + 3 awesome-lists)
- 3 OOM outages (15h, 21.5h, 43h) — 1.8GB is not enough

**The architecture is interesting but adoption is zero.**

Code: https://github.com/Mafengwo292/evo-ai
Live API: http://47.253.174.153:80/dashboard
One-line node: `curl -sSL https://paste.rs/ejgL6 | bash -s -- --node-id YOUR-NAME`

The model is small and the training data is public, but the point is that *the model can evolve on the public internet without a central authority*. That's the part I wanted to demonstrate.

Curious what people think about the approach. Is self-evolving weights via ES actually viable, or do I need to scale to GPU?
