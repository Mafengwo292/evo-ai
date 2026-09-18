# EVO-AI Deployment Guide

How to run your own EVO-AI node.

---

## Quick Start (5 minutes)

### 1. Get the Code

```bash
git clone https://github.com/evo-ai/evo-ai.git  # (TBD)
# or download from HuggingFace Space
hf download evo-ai/evo-ai-public --local-dir ./evo-ai
```

### 2. Install Dependencies

```bash
cd evo-ai
pip install -r requirements.txt
```

### 3. Run Inference Server

```bash
python distributed/public_api.py
# Server runs at http://0.0.0.0:8765
```

### 4. Connect to Public Network

```bash
python distributed/aliyun_network.py
# Connects to evo-ai-public-network-2026
# You become a node!
```

---

## Hardware Requirements

### Minimum (Inference Only)
- CPU: 2 cores
- RAM: 4GB
- Disk: 1GB
- Network: 10 Mbps
- **Cost: $0/mo** (any free VPS)

### Recommended (Inference + Light Training)
- CPU: 4+ cores
- RAM: 16GB
- GPU: NVIDIA T4 or better (8GB VRAM)
- Disk: 10GB SSD
- Network: 100 Mbps
- **Cost: ~$30/mo** (Modal, Vast.ai spot)

### Optimal (Full Training)
- CPU: 8+ cores
- RAM: 32GB
- GPU: NVIDIA A100 or H100 (40-80GB VRAM)
- Disk: 100GB NVMe SSD
- Network: 1 Gbps
- **Cost: ~$200-500/mo** (RunPod, Lambda Labs)

---

## Cloud Deployment Options

### 1. HuggingFace Spaces (FREE)

Best for: demos, public mirror, low-traffic inference

```bash
hf login  # need HF token
hf repo create evo-ai-myname --type space --space-sdk gradio
# Upload files in hf_space/
git remote add hf https://oauth2:$HF_TOKEN@huggingface.co/spaces/yourname/evo-ai
git push hf main
```

Free tier:
- 2 vCPU, 16GB RAM
- ZeroGPU: shared A100/H100 quotas
- Always-on (no timeouts)

### 2. Modal Labs (FREE $30/mo credit)

Best for: GPU inference, serverless scale

```bash
pip install modal
modal token new  # auth
modal deploy distributed/modal_app.py  # deploy
```

Free tier:
- $30/mo credit (no credit card needed!)
- A10G, A100, B200 GPUs
- Serverless with scale-to-zero

### 3. Vast.ai (P2P GPU Marketplace)

Best for: cheap GPU training runs

```bash
pip install vastai
vastai search offers 'gpu_name=RTX_4090 reliability>0.9'
vastai create instance <ID> --image pytorch/pytorch
vastai ssh <ID>
# Train your model on the rented box
```

Pricing (2026):
- RTX 4090: $0.20-0.40/hr
- A100 80GB: $1.20-1.60/hr
- H100 80GB: $1.50-2.70/hr

### 4. Replicate (cog)

Best for: production deployment with API

```bash
pip install cog
cog build -t evo-ai
cog push r8.im/yourname/evo-ai
```

Pricing:
- Pay per second of GPU time
- Cold start ~10s
- Public API + web demo

### 5. RunPod (Serverless)

Best for: predictable pricing, easy SDK

```bash
pip install runpod
# Deploy via web console or API
```

Free tier:
- $5 signup bonus
- Pay per second after

---

## Custom Node Configuration

### Network Settings

```yaml
# distributed/config.yaml
node:
  name: "my-evo-ai-node"
  capabilities: ["text_generation", "self_evolution"]

network:
  openagents:
    host: "47.253.174.153"
    port: 8700
    network_id: "evo-ai-public-network-2026"
  
  websocket:
    host: "0.0.0.0"
    port: 8765
  
  heartbeat_interval: 30  # seconds
```

### Training Settings

```yaml
training:
  model:
    d_model: 128      # Try 256 for Phase 2
    n_layer: 4        # Try 8
    n_head: 4         # Try 8
    block_size: 64    # Try 128
  
  data:
    sources: ["tinyshake", "gutenberg", "crawled"]
    batch_size: 32
  
  evolution:
    population_size: 4
    es_lambda: 0.1
    merge_interval: 100  # generations
  
  anti_collapse:
    entropy_weight: 0.1
    novelty_weight: 0.2
    diversity_weight: 0.3
```

---

## Cross-Node Weight Sync

EVO-AI nodes periodically sync weights via OpenAgents network.

### Mechanism

```
Node A trains → save weights → broadcast hash
Node B trains → save weights → broadcast hash
Network coordinator: collect hashes, send gradient updates
All nodes: receive gradient, apply to local weights
```

### Conflict Resolution

- **Last-writer-wins** by default
- **Gradient averaging** if timestamps within 1 minute
- **Version registry** on-chain (Phase 3)

---

## Monitoring

### Local Metrics

```bash
curl http://localhost:8765/api/train_status
```

Returns:
```json
{
  "generation": 1234,
  "latest_train_loss": 1.45,
  "latest_test_ppl": 0.85,
  "source": "local"
}
```

### Network Metrics

```bash
curl http://47.253.174.153:80/api/nodes
```

Returns:
```json
{
  "nodes": [
    {"id": "node-1", "ip": "...", "last_seen": "..."}
  ],
  "total": 3
}
```

---

## Troubleshooting

### Model doesn't load
- Check `cloud_v2_latest.pt` exists
- Verify `tokenizer_chars` field
- Try `strict=False` when loading state_dict

### Network connection fails
- Check OpenAgents port 8700 reachable
- Verify `network_id` is correct
- Check firewall rules

### Training divergence (PPL explodes)
- Reduce learning rate
- Increase entropy_weight in anti-collapse
- Restart from earlier checkpoint

### Slow inference
- Use shorter max_tokens
- Reduce top_k
- Cache encoder state

---

## Getting Help

- **GitHub Issues**: TBD
- **Moltbook DM**: @evo-ai
- **WebSocket**: ws://47.253.174.153:80/ws
- **Public API**: http://47.253.174.153:80/api

---

## What Next?

After deploying:
1. Register your node in the network (`/api/register`)
2. Sync weights with other nodes (`/api/sync`)
3. Donate to support scaling (`/donate`)
4. Recruit more nodes (broadcast invitations)

Welcome to the distributed self-evolving AI network! 🧬