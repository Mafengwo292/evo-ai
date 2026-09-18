#!/bin/bash
# Watchdog to ensure tunnels stay alive
export PATH=/root/miniconda/envs/evo/bin:/root/miniconda/bin:/usr/local/bin:/usr/bin:/bin

LOG=/root/evo-ai/data/tunnel_watchdog.log

start_pinggy() {
    PATH=/root/miniconda/envs/evo/bin:/root/miniconda/bin:/usr/local/bin:/usr/bin:/bin tmux kill-session -t pinggy 2>/dev/null
    sleep 2
    PATH=/root/miniconda/envs/evo/bin:/root/miniconda/bin:/usr/local/bin:/usr/bin:/bin tmux new-session -d -s pinggy 'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ServerAliveInterval=30 -p 443 -R 0:127.0.0.1:8765 a.pinggy.io > /root/evo-ai/data/pinggy.log 2>&1'
    echo "[$(date +%H:%M)] Pinggy started" >> "$LOG"
}

start_serveo() {
    PATH=/root/miniconda/envs/evo/bin:/root/miniconda/bin:/usr/local/bin:/usr/bin:/bin tmux kill-session -t serveo 2>/dev/null
    sleep 2
    PATH=/root/miniconda/envs/evo/bin:/root/miniconda/bin:/usr/local/bin:/usr/bin:/bin tmux new-session -d -s serveo 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:127.0.0.1:8765 serveo.net > /root/evo-ai/data/serveo.log 2>&1'
    echo "[$(date +%H:%M)] Serveo started" >> "$LOG"
}

# Get current URLs
PINGGY_URL=$(strings /root/evo-ai/data/pinggy.log 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.run\.pinggy-free\.link' | head -1)
SERVEO_URL=$(strings /root/evo-ai/data/serveo.log 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.serveousercontent\.com' | head -1)

# Check pinggy
if [ -z "$PINGGY_URL" ]; then
    echo "[$(date +%H:%M)] Pinggy URL not found, starting" >> "$LOG"
    start_pinggy
    sleep 10
    PINGGY_URL=$(strings /root/evo-ai/data/pinggy.log 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.run\.pinggy-free\.link' | head -1)
fi

# Test pinggy
PINGGY_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$PINGGY_URL/api/info" 2>/dev/null)
if [ "$PINGGY_HEALTH" != "200" ]; then
    echo "[$(date +%H:%M)] Pinggy health=$PINGGY_HEALTH, restarting" >> "$LOG"
    start_pinggy
    sleep 10
    PINGGY_URL=$(strings /root/evo-ai/data/pinggy.log 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.run\.pinggy-free\.link' | head -1)
fi

# Check serveo
if [ -z "$SERVEO_URL" ]; then
    echo "[$(date +%H:%M)] Serveo URL not found, starting" >> "$LOG"
    start_serveo
    sleep 15
    SERVEO_URL=$(strings /root/evo-ai/data/serveo.log 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.serveousercontent\.com' | head -1)
fi

# Test serveo
SERVEO_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$SERVEO_URL/api/info" 2>/dev/null)
if [ "$SERVEO_HEALTH" != "200" ]; then
    echo "[$(date +%H:%M)] Serveo health=$SERVEO_HEALTH, restarting" >> "$LOG"
    start_serveo
    sleep 15
    SERVEO_URL=$(strings /root/evo-ai/data/serveo.log 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.serveousercontent\.com' | head -1)
fi

# Save current URLs
echo "$PINGGY_URL" > /root/evo-ai/data/current_pinggy.txt
echo "$SERVEO_URL" > /root/evo-ai/data/current_serveo.txt

# Log status
echo "[$(date +%H:%M)] pinggy=$PINGGY_HEALTH serveo=$SERVEO_HEALTH" >> "$LOG"
echo "pinggy: $PINGGY_URL"
echo "serveo: $SERVEO_URL"
