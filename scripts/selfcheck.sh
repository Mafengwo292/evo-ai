#!/bin/bash
# EVO-AI Self Check - 每 120 分钟运行
# 全面检查：API health, OpenAgents, EVO stats, donations, training, nodes

set -e
cd /root/evo-ai
DATE=$(date '+%Y-%m-%d %H:%M:%S')
LOG=/root/evo-ai/data/selfcheck.log

echo "=========================================" | tee -a $LOG
echo "  EVO-AI SELF-CHECK @ $DATE" | tee -a $LOG
echo "=========================================" | tee -a $LOG

# 1. API health
HEALTH=$(curl -s --max-time 5 -o /dev/null -w "%{http_code}" http://127.0.0.1:8765/api/info)
echo "[1] API health: $HEALTH" | tee -a $LOG

# 2. Public endpoints
for ep in /api/info /api/evo/stats /donate /token /api/donate/stats /api/join/instructions /.well-known/agent.json /proposal /roadmap /deploy /docs; do
    CODE=$(curl -s --max-time 5 -o /dev/null -w "%{http_code}" http://127.0.0.1:8765$ep)
    echo "  $ep: $CODE" | tee -a $LOG
done

# 3. OpenAgents network
OA_CODE=$(timeout 3 bash -c "</dev/tcp/127.0.0.1/8700" && echo "UP" || echo "DOWN")
echo "[2] OpenAgents: $OA_CODE" | tee -a $LOG

# 4. EVO stats
EVO=$(curl -s --max-time 5 http://127.0.0.1:8765/api/evo/stats)
echo "[3] EVO: $(echo $EVO | python3 -c 'import json,sys;d=json.load(sys.stdin);print("minted="+str(d["minted"])+", accounts="+str(d["accounts"])+", nodes="+str(d["nodes"]))')" | tee -a $LOG

# 5. Donations
DONATE=$(curl -s --max-time 5 http://127.0.0.1:8765/api/donate/stats)
echo "[4] Donations: $(echo $DONATE | python3 -c 'import json,sys;d=json.load(sys.stdin);print("total=¥"+str(d["total_amount"])+", count="+str(d["total_count"]))')" | tee -a $LOG

# 6. tmux sessions
echo "[5] tmux sessions: $(tmux ls 2>/dev/null | wc -l)" | tee -a $LOG
echo "  $(tmux ls 2>/dev/null | tr '\n' ' ')" | tee -a $LOG

# 7. Model checkpoint
MODEL_FILE=/root/evo-ai/data/cloud_v2_latest.pt
if [ -f "$MODEL_FILE" ]; then
    SIZE=$(stat -c%s "$MODEL_FILE")
    MTIME=$(stat -c%y "$MODEL_FILE")
    echo "[6] Model: $SIZE bytes, modified $MTIME" | tee -a $LOG
else
    echo "[6] Model: MISSING" | tee -a $LOG
fi

# 8. Disk usage
DISK=$(df -h /root | tail -1)
echo "[7] Disk: $DISK" | tee -a $LOG

# 9. Memory
MEM=$(free -m | grep Mem)
echo "[8] Memory: $MEM" | tee -a $LOG

# 10. Top processes
echo "[9] Top CPU:" | tee -a $LOG
ps aux --sort=-%cpu | head -6 | tail -5 | tee -a $LOG

echo "" | tee -a $LOG
echo "Self-check complete." | tee -a $LOG
echo "=========================================" | tee -a $LOG
echo "" | tee -a $LOG