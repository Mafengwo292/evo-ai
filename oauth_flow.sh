#!/bin/bash
# GitHub OAuth Web Flow
# Usage: ./oauth_flow.sh <code>

if [ -z "$1" ]; then
    echo "Step 1: Open this URL in browser (you should be logged in already as Mafengwo292):"
    echo ""
    echo "https://github.com/login/oauth/authorize?client_id=178c81ef7e3e2b21ee2d&scope=repo,workflow,admin:org&state=$(date +%s)"
    echo ""
    echo "Step 2: Click 'Authorize EvoAILabs' (or whatever the app name is)"
    echo ""
    echo "Step 3: Browser redirects to https://paste.rs/callback?code=XXXXX"
    echo ""
    echo "Step 4: Run this script with the code:"
    echo "  ./oauth_flow.sh XXXXX"
    exit 0
fi

CODE="$1"
CLIENT_ID="178c81ef7e3e2b21ee2d"
CLIENT_SECRET=""  # Public client, no secret needed

# Exchange code for token
RESP=$(curl -s --max-time 30 -X POST \
    "https://github.com/login/oauth/access_token" \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -d "{\"client_id\":\"$CLIENT_ID\",\"code\":\"$CODE\"}" 2>&1)

echo "$RESP" | head -c 500
echo ""

# Extract token
TOKEN=$(echo "$RESP" | grep -oE '"access_token":"[^"]+"' | head -1 | sed 's/"access_token":"//;s/"$//')
echo ""
echo "Got token: ${TOKEN:0:30}..."

if [ -n "$TOKEN" ]; then
    # Test
    curl -s --max-time 15 \
        -H "Authorization: token $TOKEN" \
        "https://api.github.com/user" 2>&1 | head -c 300
fi
