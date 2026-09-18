#!/bin/bash
# EVO Token continuous broadcast loop
# Auto-claims node rewards + broadcasts token news every 6 hours

cd /root/evo-ai
PY=/root/miniconda/envs/evo/bin/python

echo "Starting EVO loop..."
while true; do
    echo "[$(date)] EVO cycle"
    $PY distributed/evo_heartbeat.py 2>&1 | tail -10
    echo "[$(date)] Sleeping 6h..."
    sleep 21600
done