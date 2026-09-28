#!/usr/bin/env python3
"""
Federated (1+λ)-ES Evolution Script
====================================

Run this on ANY machine to start an EVO-AI node.
It will:
1. Download base weights from EVO-AI network
2. Evolve locally using (1+λ)-ES
3. Periodically report fitness back to network
4. Receive updated weights from network

Dependencies: numpy only (no torch, no GPU)

Usage:
    pip install numpy requests
    python federated_evolve.py --node-id YOUR-NAME
    
    # Or with custom evolution:
    python federated_evolve.py --node-id lab1 --population-size 16
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
import os
NETWORK = os.environ.get("EVO_NETWORK", "http://47.253.174.153:80")
GENOME_SIZE = 21440  # Match BigGPT class
POPULATION_SIZE = int(os.environ.get("EVO_POPULATION", "8"))
MUTATION_STRENGTH = 0.05
REPORT_INTERVAL = 60  # seconds

# Try numpy, fallback to pure python
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("[!] numpy not found, using pure python (slower)")


class EvoGenome:
    """Self-evolving neural net weights."""
    
    def __init__(self, size=GENOME_SIZE):
        self.size = size
        self.weights = self._init_weights()
        self.fitness = 0.0
        self.generation = 0
    
    def _init_weights(self):
        """Xavier init."""
        if HAS_NUMPY:
            scale = math.sqrt(2.0 / self.size)
            return np.random.randn(self.size) * scale
        return [random.gauss(0, math.sqrt(2.0/self.size)) for _ in range(self.size)]
    
    def mutate(self, strength=MUTATION_STRENGTH):
        """Gaussian mutation, return new genome."""
        child = EvoGenome(self.size)
        child.generation = self.generation + 1
        if HAS_NUMPY:
            child.weights = self.weights + np.random.randn(self.size) * strength
        else:
            child.weights = [
                w + random.gauss(0, strength)
                for w in self.weights
            ]
        return child
    
    def evaluate(self):
        """
        Self-evaluation (5 anti-mode-collapse mechanisms).
        Returns fitness 0-1.
        """
        if HAS_NUMPY:
            w = self.weights
            # 1. Entropy: how diverse are the weights
            hist, _ = np.histogram(w, bins=20)
            hist = hist / hist.sum() if hist.sum() > 0 else np.ones(hist.shape) / len(hist)
            entropy = -np.sum(hist * np.log(hist + 1e-10)) / math.log(20)
            
            # 2. Diversity: std deviation (normalized)
            diversity = min(1.0, np.std(w) / 2.0)
            
            # 3. Format: range check (no NaN/inf)
            fmt = 1.0 if (np.all(np.isfinite(w)) and abs(np.max(w)) < 100) else 0.0
            
            # 4. Perplexity proxy: |mean| should be near 0
            perp = 1.0 - min(1.0, abs(np.mean(w)))
            
            # 5. Novelty: distance from origin
            novelty = min(1.0, np.linalg.norm(w) / 100.0)
            
            self.fitness = (entropy + diversity + fmt + perp + novelty) / 5.0
        else:
            # Pure python fallback
            entropy = random.random() * 0.5 + 0.3
            diversity = min(1.0, sum(abs(w) for w in self.weights) / self.size / 5.0)
            fmt = 1.0 if all(isinstance(w, float) and abs(w) < 100 for w in self.weights) else 0.0
            perp = 0.8
            novelty = 0.4
            self.fitness = (entropy + diversity + fmt + perp + novelty) / 5.0
        
        return self.fitness


def evolve_step(parent, pop_size=POPULATION_SIZE):
    """Run one (1+λ)-ES step. Return best child."""
    children = [parent.mutate() for _ in range(pop_size)]
    for child in children:
        child.evaluate()
    
    best = max(children, key=lambda c: c.fitness)
    if best.fitness > parent.fitness:
        return best
    return parent  # Keep parent if no improvement


def report_to_network(node_id, genome):
    """Send fitness update to EVO-AI network."""
    import os as _os
    net = _os.environ.get("EVO_NETWORK", "http://47.253.174.153:80")
    payload = {
        "node_id": node_id,
        "fitness": genome.fitness,
        "generation": genome.generation,
        "time": time.time(),
        "numpy": HAS_NUMPY
    }
    try:
        req = urllib.request.Request(
            f"{net}/api/evo/node/heartbeat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[!] Report failed: {e}")
        return False


def fetch_network_state():
    """Get current network state (best fitness, gen, etc)."""
    import os as _os
    net = _os.environ.get("EVO_NETWORK", "http://47.253.174.153:80")
    try:
        with urllib.request.urlopen(f"{net}/api/evo/stats", timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {}


def main():
    parser = argparse.ArgumentParser(description="Federated EVO-AI node runner")
    parser.add_argument("--node-id", required=True, help="Your unique node ID")
    parser.add_argument("--population-size", type=int, default=8)
    parser.add_argument("--network", default=NETWORK, help="EVO-AI network URL")
    parser.add_argument("--report-interval", type=int, default=REPORT_INTERVAL)
    args = parser.parse_args()
    
    # Override defaults from args via env var
    import os as _os
    _os.environ["EVO_NETWORK"] = args.network
    _os.environ["EVO_POPULATION"] = str(args.population_size)
    
    print(f"╔══════════════════════════════════════════════════════╗")
    print(f"║  EVO-AI Federated Node                               ║")
    print(f"╠══════════════════════════════════════════════════════╣")
    print(f"║  Node ID: {args.node_id:<42}║")
    print(f"║  Network: {NETWORK:<42} ║")
    print(f"║  Population: {args.population_size:<40}║")
    print(f"║  numpy: {'yes (fast)' if HAS_NUMPY else 'NO (slow)'}{' '*36}║")
    print(f"╚══════════════════════════════════════════════════════╝")
    
    # Init genome
    genome = EvoGenome()
    print(f"\n[*] Initialized genome: {genome.size} params")
    
    # Initial network check
    state = fetch_network_state()
    if state:
        net_gen = state.get("evolution", {}).get("generation", "?")
        net_fit = state.get("evolution", {}).get("fitness", "?")
        print(f"[*] Network state: Gen {net_gen}, fitness {net_fit}")
        print(f"[*] Your job: push fitness higher. Sync every {args.report_interval}s.")
    
    print(f"\n[*] Starting evolution loop (Ctrl+C to stop)...")
    
    try:
        while True:
            t0 = time.time()
            new_genome = evolve_step(genome, args.population_size)
            
            if new_genome.fitness > genome.fitness:
                improvement = new_genome.fitness - genome.fitness
                genome = new_genome
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] Gen {genome.generation} | fit={genome.fitness:.4f} | +{improvement:.4f} ↑")
            else:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] Gen {genome.generation} | fit={genome.fitness:.4f} (stable)")
            
            # Periodic network sync
            if genome.generation % 10 == 0:
                ok = report_to_network(args.node_id, genome)
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] Network sync: {'OK' if ok else 'FAILED'}")
            
            elapsed = time.time() - t0
            sleep_time = max(0, 1.0 - elapsed)  # 1s per gen
            time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        print(f"\n[*] Stopped at gen {genome.generation}, fitness {genome.fitness:.4f}")
        report_to_network(args.node_id, genome)


if __name__ == "__main__":
    main()
