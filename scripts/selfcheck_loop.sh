#!/bin/bash
# EVO-AI 120-minute self-check loop

cd /root/evo-ai
while true; do
    bash /root/evo-ai/scripts/selfcheck.sh 2>&1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sleeping 120 minutes..."
    sleep 7200
done