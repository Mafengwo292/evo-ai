#!/usr/bin/env python3
"""Publishes best weights metadata for federated nodes to evolve from."""
import json
import os
import struct
from datetime import datetime

GENOME_LOG = "/root/evo-ai/data/light_evo_log.jsonl"
OUT_FILE = "/root/evo-ai/data/best_weights.json"
GENOME_SIZE = 21440

def main():
    try:
        with open(GENOME_LOG) as f:
            lines = f.readlines()
        if not lines:
            print("No evolution log yet")
            return
        
        latest = json.loads(lines[-1])
        gen = latest.get('generation', 1)
        fit = latest.get('fitness', 0.0)
        
        # Generate reproducible weights based on gen (seeded random)
        # This is a synthetic placeholder - actual weights are in torch state files
        # Federated nodes will use these as starting point and mutate them
        import random
        import math
        random.seed(gen)
        weights = [random.gauss(0, math.sqrt(2.0/GENOME_SIZE)) for _ in range(GENOME_SIZE)]
        
        # Save as JSON
        data = {
            "generation": gen,
            "fitness": fit,
            "training_chars": latest.get('training_chars', 50000),
            "vocab_size": latest.get('vocab_size', 100),
            "timestamp": datetime.now().isoformat(),
            "size": GENOME_SIZE,
            "weights": weights,
            "note": f"Synthetic reproducible weights from gen {gen}. Federated nodes should evolve these."
        }
        
        with open(OUT_FILE, 'w') as f:
            json.dump(data, f)
        
        size_kb = os.path.getsize(OUT_FILE) / 1024
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] Published gen {gen}, fitness {fit:.4f} ({size_kb:.1f} KB)")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
