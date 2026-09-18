#!/bin/bash
# Monitor auto_evo.py for 30 minutes, printing status every 60 seconds.
# Stops the python process cleanly at the 30-minute mark.

PID_FILE="/tmp/auto_evo.pid"
STATUS="/workspace/evo-ai/data/auto_evo_status.json"
LOG="/workspace/evo-ai/data/auto_evo_monitor.log"
DURATION=$((30 * 60))   # 1800 seconds
INTERVAL=60
START=$(date +%s)

mkdir -p "$(dirname "$LOG")"
echo "=== Auto-evo monitor started at $(date -Iseconds) ===" > "$LOG"

while true; do
    NOW=$(date +%s)
    ELAPSED=$((NOW - START))
    if [ "$ELAPSED" -ge "$DURATION" ]; then
        echo "" | tee -a "$LOG"
        echo "=== 30 minutes reached at $(date -Iseconds) — stopping auto_evo ===" | tee -a "$LOG"
        if [ -f "$PID_FILE" ]; then
            TARGET=$(cat "$PID_FILE")
            pkill -P "$TARGET" 2>/dev/null
            kill "$TARGET" 2>/dev/null
        fi
        pkill -f "auto_evo.py" 2>/dev/null
        sleep 2
        pkill -9 -f "auto_evo.py" 2>/dev/null
        echo "=== Monitor finished ===" | tee -a "$LOG"
        exit 0
    fi

    echo "" | tee -a "$LOG"
    echo "[t+${ELAPSED}s / ${DURATION}s] $(date -Iseconds)" | tee -a "$LOG"
    if [ -f "$STATUS" ]; then
        python3 - <<'PY' 2>&1 | tee -a /workspace/evo-ai/data/auto_evo_monitor.log
import json, os
try:
    with open('/workspace/evo-ai/data/auto_evo_status.json') as f:
        d = json.load(f)
    h = d.get('history', [])
    last = h[-1] if h else {}
    print(f"  Generation:        {d.get('generation', '?')}")
    print(f"  Model version:     {d.get('model_version', '?')}")
    print(f"  Global step:       {d.get('global_step', '?')}")
    print(f"  Params:            {d.get('params', '?')}")
    print(f"  Train loss (last): {d.get('latest_train_loss', '?')}")
    print(f"  Test PPL (last):   {d.get('latest_test_ppl', '?')}")
    print(f"  Avg score (last):  {d.get('latest_avg_score', '?')}")
    print(f"  Buffer size:       {d.get('buffer_size', '?')}")
    print(f"  History length:    {len(h)}")
    if last:
        print(f"  Last gen elapsed:  {last.get('elapsed_s', '?')}s")
except Exception as e:
    print(f"  status read error: {e}")
PY
    else
        echo "  status file not present" | tee -a "$LOG"
    fi

    # Still running?
    if ! pgrep -f "auto_evo.py" >/dev/null; then
        echo "  auto_evo.py process gone — exiting monitor" | tee -a "$LOG"
        exit 0
    fi

    sleep "$INTERVAL"
done
