#!/bin/bash
# EVO-AI GitHub Push Script
# Usage: ./push_to_github.sh <YOUR_PAT_TOKEN>

set -e

if [ -z "$1" ]; then
    echo "Usage: ./push_to_github.sh <YOUR_PAT_TOKEN>"
    echo "Get your PAT at: https://github.com/settings/personal-access-tokens/new"
    echo ""
    echo "Recommended scopes:"
    echo "  - Contents: write (push code)"
    echo "  - Metadata: read (auto)"
    echo "  - Actions: write (workflows)"
    echo "  - Pull requests: write (for EvoAgentX PR)"
    echo "  - Issues: write"
    exit 1
fi

PAT="$1"
USER="Mafengwo292"
REPO="evo-ai"

cd "$(dirname "$0")"

echo "=== Creating GitHub repo ==="
curl -s -X POST \
    -H "Authorization: token $PAT" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/user/repos" \
    -d "{\"name\":\"$REPO\",\"description\":\"Distributed self-evolving language model network. 813K params evolving via (1+\\\\u03bb)-ES across volunteer nodes. Public API + A2A JSON-RPC 2.0.\",\"private\":false}"

echo ""
echo "=== Pushing code ==="
git remote add origin "https://$PAT@github.com/$USER/$REPO.git"
git push -u origin main

echo ""
echo "=== Done! Repo: https://github.com/$USER/$REPO ==="

# After push, also create EvoAgentX fork + submit
echo ""
echo "=== Forking EvoAgentX for PR ==="
curl -s -X POST \
    -H "Authorization: token $PAT" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/ANative-Lab/EvoAgentX/forks"

echo ""
echo "=== Clone the fork ==="
git clone "https://$PAT@github.com/$USER/EvoAgentX.git" /tmp/EvoAgentX-fork

echo ""
echo "=== Apply EVO_AI_PR.patch ==="
cd /tmp/EvoAgentX-fork
git checkout -b evo-ai-integration
git am < /workspace/evo-ai/contrib/evoagentx/EVO_AI_PR.patch
git push origin evo-ai-integration

echo ""
echo "=== Create PR to ANative-Lab/EvoAgentX ==="
curl -s -X POST \
    -H "Authorization: token $PAT" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/ANative-Lab/EvoAgentX/pulls" \
    -d "{\"title\":\"[EVO-AI] Add EvoAILLM model class with full OpenAILLM interface\",\"body\":\"Adds EvoAILLM model class that integrates with the EVO-AI distributed self-evolving language model network via A2A protocol. See PR description for details.\",\"head\":\"$USER:evo-ai-integration\",\"base\":\"main\"}"

echo ""
echo "=== All done! ==="
