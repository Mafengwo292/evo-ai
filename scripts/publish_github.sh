#!/bin/bash
# EVO-AI GitHub 仓库一键发布脚本
# 创建你自己的 GitHub repo 并 push EVO-AI 项目

set -e

REPO_NAME="${1:-evo-ai-public}"
GITHUB_USER="${2:-evo-ai-project}"
COMMIT_MSG="${3:-EVO-AI: Distributed Self-Evolving AI Network}"

cd /root/evo-ai

echo "=================================================="
echo "  EVO-AI GitHub Repo Publisher"
echo "=================================================="
echo ""
echo "Repository: $GITHUB_USER/$REPO_NAME"
echo ""

# Check git
if ! command -v git > /dev/null; then
    echo "❌ git not installed"
    exit 1
fi

# Initialize
if [ ! -d .git ]; then
    echo "[1/5] Initializing git repo..."
    git init
    git config user.email "hu8384jian@eyou.com"
    git config user.name "EVO-AI Project"
fi

# Create README for GitHub
cp -f /root/evo-ai/GITHUB_REPO_README.md /root/evo-ai/README_GITHUB.md
mv /root/evo-ai/README_GITHUB.md /root/evo-ai/README.md 2>/dev/null || true

# Add files
echo "[2/5] Adding files..."
git add distributed/ model/ scripts/ evolution/ hf_space/
git add PROPOSAL.md ROADMAP.md DEPLOY.md TOKEN_WHITEPAPER.md
git add README.md LICENSE requirements.txt 2>/dev/null || true
git add data/ 2>/dev/null || true

# Commit
echo "[3/5] Committing..."
git commit -m "$COMMIT_MSG" --allow-empty

# Set remote
echo "[4/5] Setting remote..."
git remote remove origin 2>/dev/null || true
git remote add origin "git@github.com:$GITHUB_USER/$REPO_NAME.git"

# Push
echo "[5/5] Pushing..."
echo ""
echo "Run this to push:"
echo ""
echo "  git push -u origin main"
echo ""
echo "If repo doesn't exist, create it first:"
echo "  gh repo create $GITHUB_USER/$REPO_NAME --public --description 'EVO-AI: Distributed Self-Evolving AI Network'"
echo ""
echo "=================================================="
echo "  ✅ Ready to push"
echo "=================================================="