#!/bin/bash
# Run federated_evolve.py as a daemon
export PATH=/root/miniconda/envs/evo/bin:/root/miniconda/bin:/usr/local/bin:/usr/bin:/bin
cd /root/evo-ai/distributed

PIDFILE=/var/run/mavis-federated.pid
LOG=/root/evo-ai/data/mavis-federated.log

# Check if already running
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Already running (PID $PID)"
        exit 0
    fi
    rm -f "$PIDFILE"
fi

# Start in background
nohup python -u federated_evolve.py --node-id mavis-federated-1 --network http://127.0.0.1:8765 > "$LOG" 2>&1 &
echo $! > "$PIDFILE"

echo "Started (PID $(cat $PIDFILE))"
