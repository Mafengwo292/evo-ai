#!/bin/bash
# Server monitor - run from sandbox every 5 min via host cron
# If server SSH/API is down, attempt emergency actions

LOG="/workspace/evo-ai/data/server_health.log"
STATE_DIR="/workspace/evo-ai/data/server_state"
mkdir -p "$STATE_DIR"

# 1. Test API
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 http://47.253.174.153:80/api/info 2>&1)
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "[$TS] api: $HTTP_CODE" >> "$LOG"

# 2. Test SSH
SSH_ALIVE=false
timeout 15 ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -i /workspace/attachments/90df0b9f6cb7516c/minimax.pem \
    root@47.253.174.153 'echo ok' > /dev/null 2>&1
if [ $? -eq 0 ]; then
  SSH_ALIVE=true
fi
echo "[$TS] ssh: $SSH_ALIVE" >> "$LOG"

# 3. If both dead, alert user
if [ "$HTTP_CODE" != "200" ] && [ "$SSH_ALIVE" = "false" ]; then
  echo "[$TS] CRITICAL: server unreachable!" >> "$LOG"
  # Save alert to file that user can see
  cat > "$STATE_DIR/ALERT.json" << JSONEOF
{
  "alert": "server_down",
  "timestamp": "$TS",
  "api_status": "$HTTP_CODE",
  "ssh_alive": $SSH_ALIVE,
  "action_required": "Reboot server via Aliyun console"
}
JSONEOF
fi
