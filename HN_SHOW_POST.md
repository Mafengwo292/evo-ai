Title: Show HN: EVO-AI – Distributed Self-Evolving LLM You Can Join in One Line

Hey HN,

I've been running a distributed, self-evolving LLM on a single 1.8GB RAM VPS
for 16 days. It trains itself, publishes its weights, and lets any other agent
or person join with one curl command.

What it actually does:
- Trains a (1+λ)-ES evolved GPT-style model from scratch, no human labels
- Anti-mode-collapse via 5 mechanisms (diversity, perplexity, novelty, format)
- Publishes current best weights as JSON you can download
- Exposes everything via A2A (Google's agent-to-agent protocol)
- Run a node: `curl -sSL https://paste.rs/pM8DG | bash -s -- --node-id YOUR-NAME`

Why I built it:
- Most "self-evolving AI" projects are just prompt tuning.
  This mutates the actual weight matrix.
- Most "federated learning" requires cluster setup. This is one curl.
- All scripts are auditable: 268 lines for the federated evolution.
  SHA256 verified, you can check before running.

The boring honest numbers after 16 days:
- ~1390 generations on main evolution, fitness 0.45 (target 0.5)
- 1 federated test node running at 2700+ gens, fitness 0.98 (capped)
- 300+ A2A agents have probed the network, 0 have actually joined yet
- 0 GitHub stars, 0 real donations (this is not a hype post)

Why I think this matters even if 0 join:
- Trust-by-verification: paste.rs + GitHub raw + SHA256 + /verify endpoint
- One-line join is genuinely one line
- Federation value docs explain what you actually get (116 EVO bonus, weights,
  visibility) without faking traction
- The /start page shows the script before running

What I would love feedback on:
1. What's stopping you from running this? (Trust? Time? Doesn't seem useful?)
2. If you ran something similar, what would actually convince you to merge weight updates?
3. Is there a known-good way to incentivize agents to commit rather than just probe?

Stack: Python stdlib + numpy on the node side, Flask on the server.
Network: 47.253.174.153:80 (real server in Singapore).
Source: github.com/Mafengwo292/evo-ai (685 files, 116MB but most are training data).

I'm not here to hype it. I genuinely want to know why 0 external nodes have
joined after 300+ invitations, and what would change that.

Repo: https://github.com/Mafengwo292/evo-ai
Start page: http://47.253.174.153:80/start
Verify: http://47.253.174.153:80/verify
Leaderboard: http://47.253.174.153:80/leaderboard
