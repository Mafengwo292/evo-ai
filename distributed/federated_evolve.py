#!/usr/bin/env python3
"""
Federated (1+λ)-ES Evolution Node
=================================

Run this on ANY machine to start an EVO-AI node.
- Pulls best weights from network
- Evolves locally
- Pushes improvements back

Dependencies: numpy (no torch, no GPU)

Usage:
    pip install numpy requests
    python federated_evolve.py --node-id YOUR-NAME
"""

import argparse
import json
import os
import sys
import time
import random
import math
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Network config
import os as _os_init
NETWORK = _os_init.environ.get("EVO_NETWORK", "http://47.253.174.153:80")
GENOME_SIZE = 21440  # Match BigGPT class
POPULATION_SIZE = 8
MUTATION_STRENGTH = 0.05
SYNC_INTERVAL = 30  # generations between network syncs

# Try numpy, fallback to pure python
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def get_network_config():
    """Read network from env, fall back to default."""
    return _os_init.environ.get("EVO_NETWORK", "http://47.253.174.153:80")


class EvoGenome:
    """Self-evolving neural net weights with network sync."""
    
    def __init__(self, size=GENOME_SIZE):
        self.size = size
        self.weights = self._init_weights()
        self.fitness = 0.0
        self.generation = 0
        self.network_fitness_at_init = 0.0
    
    def _init_weights(self):
        """Xavier init."""
        if HAS_NUMPY:
            scale = math.sqrt(2.0 / self.size)
            return np.random.randn(self.size) * scale
        return [random.gauss(0, math.sqrt(2.0/self.size)) for _ in range(self.size)]
    
    def from_dict(self, d):
        """Load weights from dict."""
        w = d.get('weights', [])
        if len(w) == self.size and HAS_NUMPY:
            self.weights = np.array(w, dtype=np.float64)
            self.fitness = d.get('fitness', 0.0)
            self.generation = d.get('generation', 0)
            self.network_fitness_at_init = self.fitness
            return True
        return False
    
    def to_dict(self):
        """Export as JSON-serializable dict."""
        if HAS_NUMPY:
            return {
                'weights': self.weights.tolist(),
                'fitness': float(self.fitness),
                'generation': int(self.generation),
                'size': self.size
            }
        return {'weights': self.weights, 'fitness': self.fitness, 'generation': self.generation}
    
    def mutate(self, strength=MUTATION_STRENGTH):
        """Gaussian mutation, return new genome."""
        child = EvoGenome(self.size)
        child.generation = self.generation + 1
        child.network_fitness_at_init = self.network_fitness_at_init
        if HAS_NUMPY:
            child.weights = self.weights + np.random.randn(self.size) * strength
        else:
            child.weights = [w + random.gauss(0, strength) for w in self.weights]
        return child
    
    def evaluate(self):
        """Self-evaluation (5 anti-mode-collapse mechanisms)."""
        if HAS_NUMPY:
            w = self.weights
            hist, _ = np.histogram(w, bins=20)
            hist = hist / hist.sum() if hist.sum() > 0 else np.ones(20) / 20
            entropy = -np.sum(hist * np.log(hist + 1e-10)) / math.log(20)
            diversity = min(1.0, np.std(w) / 2.0)
            fmt = 1.0 if (np.all(np.isfinite(w)) and abs(np.max(w)) < 100) else 0.0
            perp = 1.0 - min(1.0, abs(np.mean(w)))
            novelty = min(1.0, np.linalg.norm(w) / 100.0)
            self.fitness = (entropy + diversity + fmt + perp + novelty) / 5.0
        else:
            entropy = 0.5
            diversity = 0.5
            fmt = 1.0
            perp = 0.8
            novelty = 0.4
            self.fitness = (entropy + diversity + fmt + perp + novelty) / 5.0
        return self.fitness


def evolve_step(parent, pop_size=POPULATION_SIZE):
    """Run one (1+λ)-ES step. Return best child or parent."""
    children = [parent.mutate() for _ in range(pop_size)]
    for child in children:
        child.evaluate()
    best = max(children, key=lambda c: c.fitness)
    return best if best.fitness > parent.fitness else parent


def fetch_network_state():
    """Get current network state."""
    net = get_network_config()
    try:
        with urllib.request.urlopen(f"{net}/api/evo/stats", timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {}


def fetch_best_weights():
    """Pull best weights from network."""
    net = get_network_config()
    try:
        # Try the new sync endpoint
        with urllib.request.urlopen(f"{net}/api/evo/best_weights", timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        # Fall back to local best
        return None


def report_to_network(node_id, genome, register=False):
    """Send fitness update to EVO-AI network."""
    net = get_network_config()
    endpoint = "/api/register" if register else "/api/evo/node/heartbeat"
    payload = {
        "node_id": node_id,
        "fitness": genome.fitness,
        "generation": genome.generation,
        "time": time.time(),
        "numpy": HAS_NUMPY
    }
    if not register:
        payload["weights"] = genome.to_dict() if genome.generation % 100 == 0 else None
    try:
        req = urllib.request.Request(
            f"{net}{endpoint}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[!] Report failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Federated EVO-AI node runner")
    parser.add_argument("--node-id", required=True, help="Your unique node ID")
    parser.add_argument("--population-size", type=int, default=POPULATION_SIZE)
    parser.add_argument("--network", default="http://47.253.174.153:80", help="EVO-AI network URL")
    parser.add_argument("--from-scratch", action="store_true", help="Don't fetch best weights from network")
    args = parser.parse_args()
    
    # Set network in env so all helpers use it
    _os_init.environ["EVO_NETWORK"] = args.network
    global NETWORK
    NETWORK = args.network
    
    print(f"╔══════════════════════════════════════════════════════╗")
    print(f"║  EVO-AI Federated Node v2.0                         ║")
    print(f"╠══════════════════════════════════════════════════════╣")
    print(f"║  Node ID: {args.node_id:<42}║")
    print(f"║  Network: {NETWORK:<42} ║")
    print(f"║  Population: {args.population_size:<40}║")
    print(f"║  numpy: {'yes (fast)' if HAS_NUMPY else 'NO (slow)'}{' '*36}║")
    print(f"╚══════════════════════════════════════════════════════╝")
    
    # Initial network check
    state = fetch_network_state()
    if state:
        evo = state.get("evolution", {})
        net_gen = evo.get("generation", "?")
        net_fit = evo.get("fitness", "?")
        nodes = state.get("nodes", "?")
        print(f"\n[*] State: Gen {net_gen}, fitness {net_fit}, {nodes} nodes total")
    
    # Init genome
    genome = EvoGenome()
    
    # Try to fetch best weights from network
    if not args.from_scratch:
        print("[*] Fetching best weights from network...")
        best = fetch_best_weights()
        if best and best.get('weights'):
            if genome.from_dict(best):
                print(f"  ✓ Loaded Gen {genome.generation} with fitness {genome.fitness:.4f}")
                print(f"  ✓ Will evolve from there, not from random init")
            else:
                print(f"  ! Weight size mismatch ({len(best.get('weights', []))} vs {genome.size}), starting fresh")
        else:
            print("  ! No best weights available, starting fresh")
    
    # Initial registration
    print(f"\n[*] Registering node...")
    ok = report_to_network(args.node_id, genome, register=True)
    if ok:
        print(f"  ✓ Registered: {args.node_id}")
    else:
        print(f"  ! Registration failed (will retry on next sync)")
    
    print(f"\n[*] Starting evolution loop (Ctrl+C to stop)...")
    
    last_sync_gen = 0
    try:
        while True:
            t0 = time.time()
            new_genome = evolve_step(genome, args.population_size)
            
            if new_genome.fitness > genome.fitness:
                improvement = new_genome.fitness - genome.fitness
                genome = new_genome
                ts = datetime.now().strftime("%H:%M:%S")
                pct = (genome.fitness / 0.5) * 100
                print(f"[{ts}] Gen {genome.generation:4d} | fit={genome.fitness:.4f} (+{improvement:.4f}) | {pct:.1f}%→0.5")
            
            # Periodic network sync (every SYNC_INTERVAL generations)
            if genome.generation - last_sync_gen >= SYNC_INTERVAL:
                ok = report_to_network(args.node_id, genome, register=False)
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] 📡 Network sync (gen {genome.generation}): {'OK' if ok else 'FAIL'}")
                last_sync_gen = genome.generation
            
            elapsed = time.time() - t0
            sleep_time = max(0, 1.0 - elapsed)
            time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        print(f"\n[*] Stopped at gen {genome.generation}, fitness {genome.fitness:.4f}")
        report_to_network(args.node_id, genome, register=False)


if __name__ == "__main__":
    main()
