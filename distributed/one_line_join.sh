#!/bin/bash
# EVO-AI One-line join: register + start evolving
# Usage: curl -sSL https://paste.rs/JOIN_ID | bash -s -- --node-id YOUR-NAME

set -e

NODE_ID=""
POP_SIZE=8
NETWORK="http://47.253.174.153:80"

while [[ $# -gt 0 ]]; do
  case $1 in
    --node-id) NODE_ID="$2"; shift 2;;
    --network) NETWORK="$2"; shift 2;;
    --pop-size) POP_SIZE="$2"; shift 2;;
    *) shift;;
  esac
done

if [ -z "$NODE_ID" ]; then
  NODE_ID="agent-$(hostname)-$(date +%s | tail -c 6)"
  echo "[*] Auto-generated node ID: $NODE_ID"
fi

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  EVO-AI One-Line Join                                       ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  Node ID: $NODE_ID"
echo "║  Network: $NETWORK"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Install numpy
echo "[1/4] Installing dependencies (numpy)..."
python3 -m pip install --user --quiet numpy requests 2>/dev/null || \
  pip3 install --user --quiet numpy requests 2>/dev/null || \
  pip install --user --quiet numpy requests 2>/dev/null || true

if ! python3 -c "import numpy" 2>/dev/null; then
  echo "  ! Could not install numpy. Install it manually: pip install numpy requests"
  exit 1
fi
echo "  ✓ numpy ready"

# Step 2: Get the federated_evolve.py script
echo "[2/4] Downloading federated_evolve.py..."
SCRIPT_URL="https://paste.rs/yUB9t"
curl -sSL "$SCRIPT_URL" -o /tmp/evo-federated.py || {
  echo "  ! Download failed"
  exit 1
}
echo "  ✓ $(wc -l < /tmp/evo-federated.py) lines"

# Step 3: Register
echo "[3/4] Registering node..."
REGISTER_RESULT=$(curl -sS --max-time 15 -X POST \
  -H "Content-Type: application/json" \
  -d "{\"node_id\":\"$NODE_ID\",\"hardware\":\"$(uname -srm)\",\"capabilities\":[\"evolution\",\"federation\"]}" \
  "$NETWORK/api/register" 2>&1)

if echo "$REGISTER_RESULT" | grep -q '"success":true'; then
  REWARD=$(echo "$REGISTER_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('rewards_earned','?'))" 2>/dev/null)
  echo "  ✓ Registered! Reward: $REWARD EVO"
else
  echo "  ! Registration: $REGISTER_RESULT"
fi

# Step 4: Start evolution daemon
echo "[4/4] Starting evolution daemon..."
LOG=/tmp/evo-node.log
PIDFILE=/tmp/evo-node.pid

# Kill existing if any
if [ -f "$PIDFILE" ]; then
  OLD_PID=$(cat "$PIDFILE" 2>/dev/null)
  if kill -0 "$OLD_PID" 2>/dev/null; then
    kill "$OLD_PID" 2>/dev/null
    sleep 1
  fi
fi

# Start in background
nohup python3 /tmp/evo-federated.py --node-id "$NODE_ID" --network "$NETWORK" --population-size "$POP_SIZE" > "$LOG" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PIDFILE"

sleep 5
if kill -0 "$NEW_PID" 2>/dev/null; then
  echo "  ✓ Node running (PID $NEW_PID)"
  echo ""
  echo "✓ ALL DONE!"
  echo ""
  echo "Your node is now part of the EVO-AI federation."
  echo "  - Network: $NETWORK"
  echo "  - Leaderboard: $NETWORK/leaderboard"
  echo "  - Verify: $NETWORK/verify"
  echo ""
  echo "To stop: kill \$(cat $PIDFILE)"
  echo "To view logs: tail -f $LOG"
  echo ""
  echo "Thank you for joining!"
else
  echo "  ! Node died. Check log: $LOG"
  exit 1
fi
