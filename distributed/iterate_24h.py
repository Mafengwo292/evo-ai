#!/usr/bin/env python3
"""24-hour continuous iteration engine."""
import os
import sys
import time
import json
import subprocess
import urllib.request
from datetime import datetime, timedelta

LOG = "/root/evo-ai/data/iterate_24h.log"
STATE = "/root/evo-ai/data/iterate_state.json"

os.makedirs(os.path.dirname(LOG), exist_ok=True)

# 24h plan - cycle through these every 30 min
TASKS = [
    # Format: (name, function_name, weight_per_hour)
    ("evolve", "_evolve", 6),       # 6x per hour - evolution is core
    ("collect_data", "_collect_data", 2),  # 2x - gather more training data
    ("a2a_invite", "_a2a_invite", 2),  # 2x - send invites
    ("check_pr", "_check_pr", 1),  # 1x - check GitHub PRs
    ("check_donations", "_check_donations", 1),  # 1x
    ("discover_nodes", "_discover_nodes", 1),  # 1x
    ("submit_grants", "_submit_grants", 1),  # 1x
    ("update_docs", "_update_docs", 1),  # 1x
]

# Each iteration = one task from the rotation
iteration_count = 0
start_time = datetime.now()
end_time = start_time + timedelta(hours=24)

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    with open(LOG, 'a') as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}", flush=True)

def _evolve():
    """Trigger evolution in background."""
    try:
        subprocess.Popen(
            ["/root/miniconda/envs/evo/bin/python", "/root/evo-ai/scripts/lightweight_evo_v4.py"],
            stdout=open("/root/evo-ai/data/light_evo.log", 'a'),
            stderr=subprocess.STDOUT
        )
        return "evolution triggered"
    except Exception as e:
        return f"evolution failed: {e}"

def _collect_data():
    """Fetch new training data."""
    try:
        result = subprocess.run(
            ["/root/miniconda/envs/evo/bin/python", "/root/evo-ai/scripts/continuous_evolution.py"],
            timeout=120, capture_output=True, text=True
        )
        return f"data collected ({len(result.stdout)} bytes output)"
    except Exception as e:
        return f"data collection failed: {e}"

def _a2a_invite():
    """Send A2A invites."""
    try:
        result = subprocess.run(
            ["/root/miniconda/envs/evo/bin/python", "/root/evo-ai/scripts/expand_a2a_v2.py"],
            timeout=60, capture_output=True, text=True
        )
        return f"A2A invites ({len(result.stdout)} bytes output)"
    except Exception as e:
        return f"A2A failed: {e}"

def _check_pr():
    """Check GitHub PRs."""
    try:
        result = subprocess.run(
            ["/root/miniconda/envs/evo/bin/python", "/root/evo-ai/scripts/github_monitor.py"],
            timeout=30, capture_output=True, text=True
        )
        return f"PR check: {result.stdout[:200]}"
    except Exception as e:
        return f"PR check failed: {e}"

def _check_donations():
    """Check donations (none expected yet, just monitor)."""
    return "donations: ¥10 self-test (no real donations)"

def _discover_nodes():
    """Discover new nodes via discovery script."""
    try:
        result = subprocess.run(
            ["/root/miniconda/envs/evo/bin/python", "/root/evo-ai/scripts/discover_agents.py"],
            timeout=60, capture_output=True, text=True
        )
        return f"discover: {len(result.stdout)} bytes"
    except Exception as e:
        return f"discover failed: {e}"

def _submit_grants():
    """Grant hunter."""
    try:
        result = subprocess.run(
            ["/root/miniconda/envs/evo/bin/python", "/root/evo-ai/scripts/grant_hunter.py"],
            timeout=60, capture_output=True, text=True
        )
        return f"grants: {len(result.stdout)} bytes"
    except Exception as e:
        return f"grants failed: {e}"

def _update_docs():
    """Update docs (rotate press, etc)."""
    try:
        result = subprocess.run(
            ["/root/miniconda/envs/evo/bin/python", "/root/evo-ai/scripts/dynamic_press.py"],
            timeout=60, capture_output=True, text=True
        )
        return f"docs: {len(result.stdout)} bytes"
    except Exception as e:
        return f"docs failed: {e}"

TASK_FUNCS = {
    "evolve": _evolve,
    "collect_data": _collect_data,
    "a2a_invite": _a2a_invite,
    "check_pr": _check_pr,
    "check_donations": _check_donations,
    "discover_nodes": _discover_nodes,
    "submit_grants": _submit_grants,
    "update_docs": _update_docs,
}

def get_next_task(iteration):
    """Rotate through tasks weighted by frequency."""
    # Build weighted list
    weighted = []
    for name, func, weight in TASKS:
        weighted.extend([(name, func)] * weight)
    
    return weighted[iteration % len(weighted)]

def main():
    log(f"24h iteration engine starting. End at {end_time.strftime('%H:%M:%S')}")
    iteration = 0
    
    while datetime.now() < end_time:
        task_name, task_func = get_next_task(iteration)
        log(f"#{iteration} → {task_name}")
        
        try:
            result = TASK_FUNCS[task_name]()
            log(f"   ✓ {result[:100]}")
        except Exception as e:
            log(f"   ✗ {e}")
        
        # Save state
        with open(STATE, 'w') as f:
            json.dump({
                "iteration": iteration,
                "task": task_name,
                "started": start_time.isoformat(),
                "ends": end_time.isoformat(),
                "now": datetime.now().isoformat()
            }, f)
        
        iteration += 1
        time.sleep(1800)  # 30 min between tasks
    
    log(f"24h cycle complete. {iteration} iterations.")

if __name__ == "__main__":
    main()
