#!/bin/bash
# Watchdog: check + auto-recover all key services
LOG=/root/evo-ai/data/watchdog.log
TS=$(date "+%Y-%m-%d %H:%M:%S")
echo "[$TS] Watchdog check..." >> $LOG

# 1. API server
if ! curl -s -o /dev/null -w "" --max-time 5 http://127.0.0.1:8765/api/info 2>/dev/null; then
    echo "[$TS] API DOWN, restarting..." >> $LOG
    pkill -f public_api.py 2>/dev/null
    sleep 2
    /usr/bin/tmux kill-session -t api 2>/dev/null
    cd /root/evo-ai
    /usr/bin/tmux new-session -d -s api "/root/miniconda/envs/evo/bin/python -u /root/evo-ai/distributed/public_api.py > /root/evo-ai/data/api.log 2>&1"
    echo "[$TS] API restarted" >> $LOG
fi

# 2. evo-test daemon
if ! /usr/bin/tmux has-session -t evo-test 2>/dev/null; then
    echo "[$TS] evo-test DOWN, restarting..." >> $LOG
    /usr/bin/tmux new-session -d -s evo-test "/root/start_evo_test.sh"
    sleep 3
    echo "[$TS] evo-test restarted" >> $LOG
fi

# 3. Publisher deduplication
PUB_COUNT=$(ps aux | grep "evo_node_publisher" | grep -v grep | wc -l)
if [ "$PUB_COUNT" -lt 1 ]; then
    echo "[$TS] publisher MISSING, starting..." >> $LOG
    /usr/bin/tmux new-session -d -s evo-pub "/root/evo-ai/scripts/launch_evo_pub.sh"
elif [ "$PUB_COUNT" -gt 1 ]; then
    echo "[$TS] publisher DUPLICATES ($PUB_COUNT), killing..." >> $LOG
    PIDS=$(ps aux | grep "evo_node_publisher" | grep -v grep | awk "{print \$2}" | tail -n +2)
    for pid in $PIDS; do
        kill -9 $pid 2>/dev/null
    done
fi

# 4. Serveo tunnel (rotating URL)
if [ -f /root/evo-ai/data/serveo.log ]; then
    SERVE_URL=$(strings /root/evo-ai/data/serveo.log 2>/dev/null | grep -oE "https://[a-z0-9-]+-47-253-174-153\.serveousercontent\.com" | tail -1)
    if [ -n "$SERVE_URL" ]; then
        SERVE_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$SERVE_URL/api/info" 2>/dev/null)
        if [ "$SERVE_HEALTH" != "200" ]; then
            echo "[$TS] serveo DOWN ($SERVE_HEALTH), restarting..." >> $LOG
            /usr/bin/tmux kill-session -t serveo 2>/dev/null
            sleep 3
            /usr/bin/tmux new-session -d -s serveo "ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -R 80:127.0.0.1:8765 serveo.net > /root/evo-ai/data/serveo.log 2>&1"
            sleep 25
            NEW_URL=$(strings /root/evo-ai/data/serveo.log 2>/dev/null | grep -oE "https://[a-z0-9-]+-47-253-174-153\.serveousercontent\.com" | tail -1)
            if [ -n "$NEW_URL" ]; then
                # Update evo-node default URL
                sed -i "s#DEFAULT_NETWORK = .*#DEFAULT_NETWORK = \"$NEW_URL\"#" /root/evo-ai/dist/node/evo-node
                echo "[$TS] serveo restarted: $NEW_URL" >> $LOG
            fi
        fi
    else
        echo "[$TS] serveo URL missing, restarting..." >> $LOG
        /usr/bin/tmux kill-session -t serveo 2>/dev/null
        sleep 3
        /usr/bin/tmux new-session -d -s serveo "ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -R 80:127.0.0.1:8765 serveo.net > /root/evo-ai/data/serveo.log 2>&1"
    fi
fi

# 5. Pinggy tunnel
if [ -f /root/evo-ai/data/pinggy.log ]; then
    PING_URL=$(strings /root/evo-ai/data/pinggy.log 2>/dev/null | grep -oE "https://[a-z0-9-]+-47-253-174-153\.(run\.pinggy-free\.link|free\.pinggy\.net)" | tail -1)
    if [ -n "$PING_URL" ]; then
        PING_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$PING_URL/api/info" 2>/dev/null)
        if [ "$PING_HEALTH" != "200" ]; then
            echo "[$TS] pinggy DOWN ($PING_HEALTH), restarting..." >> $LOG
            /usr/bin/tmux kill-session -t pinggy 2>/dev/null
            sleep 3
            /usr/bin/tmux new-session -d -s pinggy "ssh -p 443 -R 0:127.0.0.1:8765 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes a.pinggy.io > /root/evo-ai/data/pinggy.log 2>&1"
        fi
    fi
fi

# 6. Kill zombie cloudflared
ZOMBIE=$(ps aux | grep cloudflared | grep -v grep | wc -l)
if [ "$ZOMBIE" -gt 3 ]; then
    echo "[$TS] cloudflared zombies ($ZOMBIE), killing..." >> $LOG
    pkill -9 -f cloudflared 2>/dev/null
fi

# 7. Kill duplicate cron-spawned evo-publishers (cleanup)
P_COUNT=$(ps aux | grep evo_node_publisher | grep -v grep | wc -l)
if [ "$P_COUNT" -gt 3 ]; then
    pkill -9 -f evo_node_publisher 2>/dev/null
    /usr/bin/tmux kill-session -t evo-pub 2>/dev/null
    /usr/bin/tmux new-session -d -s evo-pub "/root/evo-ai/scripts/launch_evo_pub.sh"
    echo "[$TS] reset evo-pub (had $P_COUNT)" >> $LOG
fi

echo "[$TS] Done" >> $LOG
