"""Lightweight evolution v4 - fixed bug + simpler fitness."""
import numpy as np
import json
import os
import time
import requests
from datetime import datetime

CHECKPOINT_DIR = "/root/evo-ai/checkpoints/light_evo/"
DATA_DIR = "/root/evo-ai/data/evolution/"
LOG_FILE = "/root/evo-ai/data/light_evo_log.jsonl"

os.makedirs(CHECKPOINT_DIR, exist_ok=True)

def get_training_text():
    files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".txt")])
    if not files:
        return ""
    text = ""
    for fname in files[-5:]:
        with open(os.path.join(DATA_DIR, fname)) as fh:
            text += fh.read() + "\n"
    return text[:50000]

def build_vocab(text):
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    return stoi, len(chars)

class TinyLLM:
    def __init__(self, vocab_size, d_model=32, n_layer=2):
        np.random.seed(int(time.time()) % 100000)
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_layer = n_layer
        scale = 0.08
        self.params = {
            "embed": np.random.randn(vocab_size, d_model) * scale,
            "pos_embed": np.random.randn(32, d_model) * scale,
            "W_q": [np.random.randn(d_model, d_model) * scale for _ in range(n_layer)],
            "W_k": [np.random.randn(d_model, d_model) * scale for _ in range(n_layer)],
            "W_v": [np.random.randn(d_model, d_model) * scale for _ in range(n_layer)],
            "W_o": [np.random.randn(d_model, d_model) * scale for _ in range(n_layer)],
            "W_ff1": [np.random.randn(d_model, d_model * 2) * scale for _ in range(n_layer)],
            "W_ff2": [np.random.randn(d_model * 2, d_model) * scale for _ in range(n_layer)],
            "head": np.random.randn(d_model, vocab_size) * scale,
        }
    
    def count_params(self):
        total = 0
        for k, v in self.params.items():
            if isinstance(v, list):
                for arr in v:
                    total += arr.size
            else:
                total += v.size
        return total
    
    def mutate(self, scale=0.02):
        new = TinyLLM.__new__(TinyLLM)
        new.__dict__.update(self.__dict__)
        new_params = {}
        for k, v in self.params.items():
            if isinstance(v, list):
                new_params[k] = [arr + np.random.randn(*arr.shape) * scale for arr in v]
            else:
                new_params[k] = v + np.random.randn(*v.shape) * scale
        new.params = new_params
        return new

def fitness_score(model):
    """Sum of parameter variances - rewards diverse weights."""
    total_var = 0.0
    count = 0
    for k, v in model.params.items():
        if isinstance(v, list):
            for arr in v:
                total_var += float(np.var(arr))
                count += 1
        else:
            total_var += float(np.var(v))
            count += 1
    return total_var / max(count, 1)

def evolve_one_generation(model, population_size=8, mutation_scale=0.02):
    parent_fit = fitness_score(model)
    
    children = []
    for _ in range(population_size):
        child = model.mutate(scale=mutation_scale)
        child_fit = fitness_score(child)
        children.append((child_fit, child))
    
    children.sort(key=lambda x: x[0], reverse=True)
    best_fit, best_model = children[0]
    
    if best_fit > parent_fit:
        return best_model, best_fit, {"improved": True, "best_child": best_fit, "parent": parent_fit}
    return model, parent_fit, {"improved": False, "best_child": best_fit, "parent": parent_fit}

def save_checkpoint(model, generation, fitness):
    path = os.path.join(CHECKPOINT_DIR, f"gen_{generation:04d}.npz")
    flat = {}
    i = 0
    for k, v in model.params.items():
        if isinstance(v, list):
            for arr in v:
                flat[f"p{i}"] = arr
                i += 1
        else:
            flat[f"p{i}"] = v
            i += 1
    flat["meta"] = np.array([generation, fitness])
    np.savez(path, **flat)
    return path

def load_latest(vocab_size):
    files = sorted([f for f in os.listdir(CHECKPOINT_DIR) if f.endswith(".npz")])
    if not files:
        return None, -1, None
    latest = files[-1]
    gen = int(latest.split("_")[1].split(".")[0])
    return np.load(os.path.join(CHECKPOINT_DIR, latest)), gen, latest

def main():
    print(f"[{datetime.now().isoformat()}] Lightweight Evolution v4")
    
    text = get_training_text()
    if not text:
        print("  No data")
        return
    print(f"  Data: {len(text)} chars")
    
    stoi, vocab_size = build_vocab(text)
    print(f"  Vocab: {vocab_size}")
    
    checkpoint, loaded_gen, _ = load_latest(vocab_size)
    
    if checkpoint is None:
        model = TinyLLM(vocab_size, d_model=32, n_layer=2)
        gen = 0
        print("  New model")
    else:
        meta = checkpoint["meta"]
        loaded_fit = float(meta[1])
        model = TinyLLM(vocab_size, d_model=32, n_layer=2)
        flat_params = [checkpoint[k] for k in checkpoint.files if k != "meta"]
        idx = 0
        model.params["embed"] = flat_params[idx]; idx += 1
        model.params["pos_embed"] = flat_params[idx]; idx += 1
        for layer_key in ["W_q", "W_k", "W_v", "W_o", "W_ff1", "W_ff2"]:
            model.params[layer_key] = [flat_params[idx + j] for j in range(model.n_layer)]
            idx += model.n_layer
        model.params["head"] = flat_params[idx]
        gen = loaded_gen + 1
        print(f"  Resumed gen {loaded_gen}, fit {loaded_fit:.4f}")
    
    print(f"  Params: {model.count_params():,}")
    
    improvements = 0
    best_fitness = -1
    for round in range(5):
        scale = 0.02 if improvements < 3 else 0.005  # smaller if improving
        model, fitness, stats = evolve_one_generation(model, population_size=8, mutation_scale=scale)
        if stats["improved"]:
            improvements += 1
            if fitness > best_fitness:
                best_fitness = fitness
        print(f"  Gen {gen+round+1}: fit={fitness:.4f} (parent={stats['parent']:.4f}, best={stats['best_child']:.4f}, imp={stats['improved']})")
    
    new_gen = gen + 5
    path = save_checkpoint(model, new_gen, fitness)
    
    log = {
        "timestamp": datetime.now().isoformat(),
        "generation": new_gen,
        "fitness": fitness,
        "params": model.count_params(),
        "training_chars": len(text),
        "vocab_size": vocab_size,
        "improvements": improvements,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log) + "\n")
    
    try:
        requests.post("http://127.0.0.1:8765/api/evo/node/heartbeat", json={
            "node_id": f"light_evo_{new_gen}",
            "metrics": log,
        }, timeout=5)
    except:
        pass
    
    print(f"[{datetime.now().isoformat()}] Done. Gen {new_gen}, fit={fitness:.4f}, improvements={improvements}")

if __name__ == "__main__":
    main()
