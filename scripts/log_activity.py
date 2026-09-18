#!/usr/bin/env python3
"""
log_activity.py - 记录我每一步的操作

每次执行 action: append 到 /root/evo-ai/data/activity/YYYY-MM-DD.jsonl
"""
import os, json, time, sys

ACTIVITY_DIR = '/root/evo-ai/data/activity'
LOG_FILE = ACTIVITY_DIR + '/' + time.strftime('%Y-%m-%d') + '.jsonl'


def log(action, details=None, status='success'):
    """Log a single action"""
    os.makedirs(ACTIVITY_DIR, exist_ok=True)
    entry = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'iso': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'action': action,
        'status': status,
        'details': details or {},
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    print('LOG: ' + action + ' - ' + (status or ''))


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'unknown'
    details = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    status = sys.argv[3] if len(sys.argv) > 3 else 'success'
    log(action, details, status)