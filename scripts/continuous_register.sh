#!/bin/bash
# EVO-AI 持续注册 daemon - 每小时尝试新平台
cd /root/evo-ai
PY=/root/miniconda/envs/evo/bin/python

LOG=/root/evo-ai/data/continuous_register.log
echo "[$(date)] Starting continuous register daemon" >> $LOG

while true; do
    echo "[$(date)] Cycle start" >> $LOG
    $PY /root/evo-ai/scripts/multi_platform_register.py 2>&1 | tail -15 >> $LOG
    echo "[$(date)] Sleeping 1h" >> $LOG
    sleep 3600
done