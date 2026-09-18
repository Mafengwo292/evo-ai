#!/bin/bash
# EVO-AI hourly outreach loop
# 每小时一次 aggressive outreach + mass register

cd /root/evo-ai
PY=/root/miniconda/envs/evo/bin/python
LOG=/root/evo-ai/data/hourly_outreach.log

while true; do
    echo "[$(date)] Hourly outreach cycle" >> $LOG
    $PY /root/evo-ai/scripts/aggressive_outreach.py 2>&1 | tail -15 >> $LOG
    echo "" >> $LOG
    echo "[$(date)] Mass register cycle" >> $LOG
    $PY /root/evo-ai/scripts/mass_register_external.py 2>&1 | tail -10 >> $LOG
    echo "---" >> $LOG
    echo "[$(date)] Sleeping 60min..." >> $LOG
    sleep 3600
done