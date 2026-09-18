"""EVO-AI Long-term Autonomous Engine.
Runs hourly. Reads state, makes decisions, executes, logs.
"""
import json
import os
import time
import requests
import subprocess
from datetime import datetime

STATE_DIR = "/root/evo-ai/state/"
SCRIPTS_DIR = "/root/evo-ai/scripts/"
DATA_DIR = "/root/evo-ai/data/"
LOG_FILE = STATE_DIR + "self_drive.log"
DECISIONS_FILE = STATE_DIR + "DECISIONS.md"

os.makedirs(STATE_DIR, exist_ok=True)

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_metrics():
    """Load current metrics from JSON."""
    try:
        with open(STATE_DIR + "METRICS.json") as f:
            return json.load(f)
    except:
        return {"metrics": {}}

def save_metrics(metrics):
    metrics["last_updated"] = datetime.now().isoformat()
    with open(STATE_DIR + "METRICS.json", "w") as f:
        json.dump(metrics, f, indent=2)

def fetch_live_state():
    """Pull live data from API."""
    state = {}
    try:
        r = requests.get("http://127.0.0.1:8765/api/info", timeout=5)
        state["api_info"] = r.json() if r.status_code == 200 else None
    except:
        state["api_info"] = None
    
    try:
        r = requests.get("http://127.0.0.1:8765/api/evo/stats", timeout=5)
        state["evo_stats"] = r.json() if r.status_code == 200 else None
    except:
        state["evo_stats"] = None
    
    # Check evolution log
    try:
        with open(DATA_DIR + "light_evo_log.jsonl") as f:
            lines = f.readlines()
            if lines:
                state["last_evolution"] = json.loads(lines[-1])
    except:
        state["last_evolution"] = None
    
    # Check external traffic
    try:
        with open(DATA_DIR + "external_traffic.jsonl") as f:
            lines = f.readlines()
            state["external_traffic_entries"] = len(lines)
            state["unique_ips"] = len(set(line for line in lines))
    except:
        state["external_traffic_entries"] = 0
        state["unique_ips"] = 0
    
    # Check running processes
    try:
        result = subprocess.run(["pgrep", "-f", "light_api"], capture_output=True, text=True)
        state["api_running"] = bool(result.stdout.strip())
    except:
        state["api_running"] = False
    
    # Check memory
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if "MemAvailable" in line:
                    avail_kb = int(line.split()[1])
                    state["mem_available_mb"] = avail_kb // 1024
                    break
    except:
        state["mem_available_mb"] = 0
    
    return state

def record_decision(decision, reason, action):
    """Append to decisions log."""
    ts = datetime.now().isoformat()
    entry = f"\n## {ts}\n- **Decision**: {decision}\n- **Reason**: {reason}\n- **Action**: {action}\n"
    with open(DECISIONS_FILE, "a") as f:
        f.write(entry)

def run_action(action_name):
    """Run a specific action script and return success."""
    script_path = SCRIPTS_DIR + action_name + ".py"
    if not os.path.exists(script_path):
        return False, f"Script not found: {script_path}"
    try:
        result = subprocess.run(
            ["/root/miniconda/envs/evo/bin/python", script_path],
            capture_output=True,
            text=True,
            timeout=180,
        )
        return result.returncode == 0, result.stdout[-500:]
    except subprocess.TimeoutExpired:
        return False, "Timeout after 180s"
    except Exception as e:
        return False, str(e)

def make_decisions(state):
    """Decide what actions to take based on current state."""
    decisions = []
    
    # Decision 1: Run evolution if no recent activity
    if state.get("last_evolution"):
        last_evo_ts = state["last_evolution"].get("timestamp", "")
        try:
            last_dt = datetime.fromisoformat(last_evo_ts)
            hours_since = (datetime.now() - last_dt).total_seconds() / 3600
            if hours_since > 1.5:
                decisions.append(("evolve", "No evolution in last 1.5h"))
        except:
            decisions.append(("evolve", "Evolution timestamp malformed"))
    else:
        decisions.append(("evolve", "No evolution record found"))
    
    # Decision 2: Discover new agents if external traffic is low
    if state.get("unique_ips", 0) < 50:
        decisions.append(("discover_agents", f"Only {state.get('unique_ips', 0)} unique IPs"))
    
    # Decision 3: Always do A2A expansion
    decisions.append(("expand_a2a_v2", "Continuous A2A outreach"))
    
    # Decision 4: Refresh training data if old
    try:
        evo_files = sorted(os.listdir(DATA_DIR + "evolution/")) if os.path.exists(DATA_DIR + "evolution/") else []
        if evo_files:
            last_evo = evo_files[-1]
            file_path = DATA_DIR + "evolution/" + last_evo
            file_age = time.time() - os.path.getmtime(file_path)
            if file_age > 6 * 3600:  # > 6h
                decisions.append(("continuous_evolution", f"Training data {file_age/3600:.1f}h old"))
    except:
        pass
    
    # Decision 5: Auto-announce weekly
    decisions.append(("auto_announce", "Weekly announcement refresh"))
    
    return decisions

def main():
    log("=== self_drive cycle starting ===")
    
    # 1. Fetch state
    state = fetch_live_state()
    log(f"State: nodes={state.get('evo_stats', {}).get('nodes', '?')}, "
        f"fitness={state.get('last_evolution', {}).get('fitness', '?') if state.get('last_evolution') else 'N/A'}, "
        f"unique_ips={state.get('unique_ips', 0)}, "
        f"mem={state.get('mem_available_mb', 0)}MB")
    
    # 2. Make decisions
    decisions = make_decisions(state)
    log(f"Made {len(decisions)} decisions: {[d[0] for d in decisions]}")
    
    # 3. Execute (with limits - max 3 actions per cycle to avoid overloading)
    actions_taken = []
    for action_name, reason in decisions[:3]:
        log(f"Executing: {action_name} (reason: {reason})")
        success, output = run_action(action_name)
        if success:
            log(f"  -> OK")
            actions_taken.append(action_name)
            record_decision(f"Run {action_name}", reason, "Executed successfully")
        else:
            log(f"  -> FAILED: {output[:200]}")
            record_decision(f"Run {action_name}", reason, f"Failed: {output[:200]}")
        time.sleep(5)
    
    # 4. Update metrics
    metrics = load_metrics()
    metrics["metrics"]["external_nodes"]["total_registered"] = state.get("evo_stats", {}).get("nodes", 15)
    if state.get("last_evolution"):
        metrics["metrics"]["model_fitness"]["value"] = state["last_evolution"].get("fitness", 0)
        metrics["metrics"]["model_fitness"]["generation"] = state["last_evolution"].get("generation", 0)
    metrics["metrics"]["external_probes"]["last_24h"] = state.get("external_traffic_entries", 0)
    metrics["metrics"]["external_probes"]["unique_ips"] = state.get("unique_ips", 0)
    save_metrics(metrics)
    
    log(f"Cycle complete. Actions: {actions_taken}")
    log("=== self_drive cycle done ===\n")

if __name__ == "__main__":
    main()
