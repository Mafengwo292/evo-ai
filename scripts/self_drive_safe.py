"""Safe self_drive with concurrency lock + memory check."""
import os
import sys
import fcntl
import json
import time
import requests
import subprocess
from datetime import datetime

LOCK_FILE = "/tmp/self_drive.lock"
STATE_DIR = "/root/evo-ai/state/"
SCRIPTS_DIR = "/root/evo-ai/scripts/"
DATA_DIR = "/root/evo-ai/data/"
LOG_FILE = STATE_DIR + "self_drive.log"
DECISIONS_FILE = STATE_DIR + "DECISIONS.md"

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def main():
    # Concurrency lock
    lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("Another self_drive is running. Exit.")
        return
    
    try:
        log("=== self_drive_safe cycle starting ===")
        
        # Memory check - skip if too low
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if "MemAvailable" in line:
                        avail_mb = int(line.split()[1]) // 1024
                        break
            if avail_mb < 300:
                log(f"Memory too low ({avail_mb}MB). Skip this cycle.")
                return
            log(f"Available memory: {avail_mb}MB")
        except:
            avail_mb = 1000  # assume OK
        
        # Check if other heavy scripts are running
        try:
            result = subprocess.run(
                ["pgrep", "-fc", "expand_a2a|auto_announce|continuous_evolution|discover_agents|grant_hunter"],
                capture_output=True, text=True, timeout=5
            )
            running_count = int(result.stdout.strip()) if result.stdout.strip() else 0
            if running_count > 2:
                log(f"Too many other scripts running ({running_count}). Skip.")
                return
        except:
            pass
        
        # Run only ONE script per cycle (not 3) to reduce memory pressure
        # Rotate through them
        try:
            with open(STATE_DIR + "self_drive_counter") as f:
                counter = int(f.read().strip())
        except:
            counter = 0
        
        actions = ["expand_a2a_v2", "auto_announce", "discover_agents", "continuous_evolution", "lightweight_evo_v4"]
        action = actions[counter % len(actions)]
        counter += 1
        with open(STATE_DIR + "self_drive_counter", "w") as f:
            f.write(str(counter))
        
        script_path = SCRIPTS_DIR + action + ".py"
        log(f"Running action: {action}")
        try:
            result = subprocess.run(
                ["/root/miniconda/envs/evo/bin/python", script_path],
                capture_output=True, text=True, timeout=180
            )
            if result.returncode == 0:
                log(f"  -> OK")
            else:
                log(f"  -> FAIL: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            log(f"  -> Timeout")
        except Exception as e:
            log(f"  -> ERR: {e}")
        
        log("=== self_drive_safe cycle done ===\n")
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()

if __name__ == "__main__":
    main()
