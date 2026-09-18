# How to Push EVO-AI to GitHub

Once you provide a Personal Access Token (PAT), execute these commands:

## Setup
```bash
cd /workspace/evo-ai
git init
git add .
git commit -m "Initial: EVO-AI distributed self-evolving LLM network"
git remote add origin https://github.com/<YOUR_USERNAME>/evo-ai.git
git push -u origin main
```

## What Will Be Pushed
- All code (120MB+ repo size)
- PROPOSAL.md, ROADMAP.md, DEPLOY.md
- All scripts/ (autonomous engine)
- All grants/ applications (Anthropic, AWS, etc.)
- dist/node/ (evo-node program + light_api)
- contrib/evoagentx/ (PR ready to submit)

## After Push - Manual Steps
1. Go to repo Settings → Pages → enable from main branch
2. Add GitHub Actions workflow files (already in .github/workflows/)
3. Fork EvoAgentX repo and submit PR using contrib/evoagentx/EVO_AI_PR.patch
4. Add token to repo secrets as GH_TOKEN for A2A outreach automation
