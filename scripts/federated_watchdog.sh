#!/bin/bash
# Watchdog - restart federated node if log not updated in 30 min

LOG=/root/evo-ai/data/mavis-federated.log
SCRIPT=/root/evo-ai/scripts/run_federated_node.sh

if [ ! -f "$LOG" ]; then
    echo "[$(date +%H:%M:%S)] No log file, starting"
    /bin/bash "$SCRIPT"
    exit 0
fi

# Check mtime
MTIME=$(stat -c %Y "$LOG" 2>/dev/null)
NOW=$(date +%s)
AGE=$((NOW - MTIME))

if [ "$AGE" -gt 1800 ]; then  # 30 min
    echo "[$(date +%H:%M:%S)] Log not updated for ${AGE}s, restarting"
    # Kill old process
    pkill -9 -f federated_evolve 2>/dev/null
    sleep 2
    /bin/bash "$SCRIPT"
else
    echo "[$(date +%H:%M:%S)] OK, log age ${AGE}s"
fi
