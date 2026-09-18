#!/bin/bash
# EVO-AI 全部 daemon 一键启动
cd /root/evo-ai
PY=/root/miniconda/envs/evo/bin/python

# 1. Mass recruitment daemon (30 min cycle)
tmux new-session -d -s recruit2 "/root/miniconda/envs/evo/bin/python -u /root/evo-ai/distributed/mass_recruit_v2.py > /root/evo-ai/data/recruit2.log 2>&1"

# 2. Self-evolution daemon (60 min cycle)
tmux new-session -d -s self-evo "/root/miniconda/envs/evo/bin/python -u /root/evo-ai/distributed/evo_self_daemon.py > /root/evo-ai/data/self_evo.log 2>&1"

# 3. Donation monitor (10 min cycle)
cat > /tmp/donation_monitor.py << 'PYEOF'
import time, requests
from datetime import datetime
while True:
    try:
        r = requests.get("http://127.0.0.1:8765/api/donate/stats", timeout=5).json()
        total = r.get("total_amount", 0)
        count = r.get("total_count", 0)
        if total > 0:
            print(f"[{datetime.now()}] 🎉 Donation detected! Total: ¥{total:,.2f}, Donors: {count}")
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")
    time.sleep(600)
PYEOF
tmux new-session -d -s donate-mon "/root/miniconda/envs/evo/bin/python -u /tmp/donation_monitor.py > /root/evo-ai/data/donate_mon.log 2>&1"

echo "Started: recruit2, self-evo, donate-mon"
tmux ls | grep -E "recruit2|self-evo|donate-mon"