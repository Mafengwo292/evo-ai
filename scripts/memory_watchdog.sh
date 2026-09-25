#!/bin/bash
# Memory pressure watchdog - kill heavy processes before OOM kills sshd
LOG=/root/evo-ai/data/memory_watchdog.log
ALERT_THRESHOLD=85
KILL_THRESHOLD=92

FREE_PCT=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')
AVAIL_MB=$(free -m | awk 'NR==2 {print $7}')

echo "[$(date +%H:%M:%S)] Memory: ${FREE_PCT}% used, ${AVAIL_MB}MB available" >> "$LOG"

if [ "$FREE_PCT" -gt "$KILL_THRESHOLD" ]; then
    echo "[$(date +%H:%M:%S)] CRITICAL ${FREE_PCT}% - killing low-priority procs" >> "$LOG"
    for pid in $(ps -eo pid,pmem,cmd --sort=-pmem | grep -vE 'systemd|sshd|crond|rsyslog|aegis|aliyun|tuned|evo-api|evo-pub' | awk '$2 > 5 {print $1}' | head -3); do
        cmdline=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')
        echo "  killing $pid: $cmdline" >> "$LOG"
        kill -9 "$pid" 2>/dev/null
    done
fi

tail -200 "$LOG" > /tmp/mem.log && mv /tmp/mem.log "$LOG"
