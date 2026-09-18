#!/bin/bash
# Wait until the monitor process exits, then dump final status.
MON_PID=$(cat /workspace/evo-ai/data/auto_evo_monitor.pid 2>/dev/null)
echo "Waiting for monitor (PID=$MON_PID) to finish..."
while kill -0 $MON_PID 2>/dev/null; do
    sleep 10
done
echo "Monitor finished at $(date -Iseconds)"
echo "--- Final auto_evo_status ---"
python3 -c "
import json
with open('/workspace/evo-ai/data/auto_evo_status.json') as f: d=json.load(f)
h=d.get('history',[])
print(f'final gen={d[\"generation\"]} step={d[\"global_step\"]} loss={d[\"latest_train_loss\"]} ppl={d[\"latest_test_ppl\"]} score={d[\"latest_avg_score\"]} buf={d[\"buffer_size\"]} hist_len={len(h)}')
print('All history:')
for entry in h:
    print(f\"  gen={entry['generation']:3d} score={entry['avg_score']:.4f} loss={entry['train_loss']:.4f} ppl={entry['test_perplexity_loss']:.4f} buf={entry['buffer_size']:4d} elapsed={entry['elapsed_s']}s\")
"
echo "--- monitor log tail ---"
tail -100 /workspace/evo-ai/data/auto_evo_monitor.log
