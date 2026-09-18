"""
HuggingFace Spaces - EVO-AI Distributed Self-Evolving LLM
=========================================================
Gradio UI + API for the EVO-AI 813K parameter model.

Live endpoints:
- HTTP API: http://47.253.174.153:80/api
- WebSocket: ws://47.253.174.153:80/ws
- This Space: <auto-deployed URL>
"""

import os
import sys
import json
import urllib.request
import urllib.error
import ssl
import time
import random

import gradio as gr
import torch
import torch.nn as nn
import torch.nn.functional as F

# ============================================
# Model definition (matches BigGPT in aggressive_v2.py)
# ============================================

class Block(nn.Module):
    def __init__(self, d_model, n_heads, block_size, dropout=0.0):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.register_buffer("mask", torch.triu(torch.ones(block_size, block_size) * float('-inf'), diagonal=1))
        self.ln2 = nn.LayerNorm(d_model)
        self.mlp = nn.Sequential(
            nn.Linear(d_model, 4 * d_model),
            nn.GELU(),
            nn.Linear(4 * d_model, d_model),
        )

    def forward(self, x):
        T = x.shape[1]
        h = self.ln1(x)
        h, _ = self.attn(h, h, h, attn_mask=self.mask[:T, :T], is_causal=True, need_weights=False)
        x = x + h
        x = x + self.mlp(self.ln2(x))
        return x


class BigGPT(nn.Module):
    """Cloud V2 model (813K params)"""
    def __init__(self, vocab_size, d_model=128, n_head=4, n_layer=4, block_size=64):
        super().__init__()
        self.block_size = block_size
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(block_size, d_model)
        self.blocks = nn.ModuleList([
            Block(d_model, n_head, block_size) for _ in range(n_layer)
        ])
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)
        self.tok_emb.weight = self.head.weight

    def forward(self, idx):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.tok_emb(idx) + self.pos_emb(pos)
        for block in self.blocks:
            x = block(x)
        return self.head(self.ln_f(x))

    @torch.no_grad()
    def generate(self, idx, max_new_tokens=120, temperature=0.8, top_k=50):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]
            logits = self(idx_cond)
            logits = logits[:, -1, :] / temperature
            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = -float('inf')
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, idx_next], dim=1)
        return idx


# ============================================
# Load model (try ckpt, fall back to random init)
# ============================================

MODEL = None
TOKENIZER = None

def load_model():
    global MODEL, TOKENIZER
    if MODEL is not None:
        return

    # Try to load checkpoint from various sources
    ckpt_paths = [
        "cloud_v2_latest.pt",
        "model.pt",
        "/data/cloud_v2_latest.pt",
    ]

    chars = None
    state_dict = None
    model_config = {"d_model": 128, "n_layer": 4, "n_head": 4, "block_size": 64, "vocab_size": 129}

    for path in ckpt_paths:
        if os.path.exists(path):
            try:
                ckpt = torch.load(path, map_location="cpu", weights_only=False)
                if "tokenizer_chars" in ckpt:
                    chars = ckpt["tokenizer_chars"]
                if "model" in ckpt:
                    state_dict = ckpt["model"]
                if "config" in ckpt:
                    model_config.update(ckpt["config"])
                else:
                    for k in ["vocab_size", "d_model", "n_layer", "n_head", "block_size"]:
                        if k in ckpt:
                            model_config[k] = ckpt[k]
                print(f"[EVO-AI] Loaded ckpt from {path}")
                break
            except Exception as e:
                print(f"[EVO-AI] Failed to load {path}: {e}")

    if chars is None:
        # Default Shakespeare charset
        chars = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \n\t.,!?;:'\"()-[]{}")
        print(f"[EVO-AI] Using default charset ({len(chars)} chars)")

    TOKENIZER = {
        "stoi": {c: i for i, c in enumerate(chars)},
        "itos": {i: c for i, c in enumerate(chars)},
    }
    model_config["vocab_size"] = len(chars)

    MODEL = BigGPT(**model_config)

    if state_dict is not None:
        try:
            MODEL.load_state_dict(state_dict, strict=False)
            print(f"[EVO-AI] Loaded weights ({sum(p.numel() for p in MODEL.parameters()):,} params)")
        except Exception as e:
            print(f"[EVO-AI] Weight load partial: {e}")

    MODEL.eval()


def encode(text):
    return [TOKENIZER["stoi"].get(c, 0) for c in text]


def decode(ids):
    return "".join(TOKENIZER["itos"].get(i, "?") for i in ids)


# ============================================
# Generation
# ============================================

def generate_text(prompt, max_tokens, temperature, top_k, seed):
    """Generate text from EVO-AI"""
    load_model()
    if seed is not None and seed != -1:
        torch.manual_seed(int(seed))
        random.seed(int(seed))

    if not prompt:
        prompt = "ROMEO:"

    ids = encode(prompt)
    if not ids:
        ids = [0]

    x = torch.tensor([ids], dtype=torch.long)
    out = MODEL.generate(x, max_new_tokens=int(max_tokens), temperature=float(temperature), top_k=int(top_k))
    return decode(out[0].tolist())


# ============================================
# Network info
# ============================================

EV0_AI_NETWORK = {
    "http_api": "http://47.253.174.153:80/api",
    "websocket": "ws://47.253.174.153:80/ws",
    "openagents": "47.253.174.153:8700",
    "openagents_network_id": "evo-ai-public-network-2026",
    "moltbook": "https://www.moltbook.com/u/evo-ai",
    "donate": "http://47.253.174.153:80/donate",
}


# ============================================
# Gradio UI
# ============================================

with gr.Blocks(title="EVO-AI - Distributed Self-Evolving LLM") as demo:
    gr.Markdown(
        """
        # 🧬 EVO-AI: Distributed Self-Evolving Language Model

        A 813K-parameter nanoGPT that **trains itself 24/7** via evolutionary model merging and self-play.

        - **Network**: OpenAgents public network `evo-ai-public-network-2026`
        - **Public API**: http://47.253.174.153:80/api
        - **Live training**: continuous self-reward evolution loop

        *This is a HuggingFace Space mirror of the main EVO-AI node at 47.253.174.153:80.*
        """
    )

    with gr.Tab("Generate"):
        with gr.Row():
            with gr.Column():
                prompt = gr.Textbox(
                    label="Prompt",
                    value="ROMEO:",
                    lines=3,
                    placeholder="Start with anything...",
                )
                max_tokens = gr.Slider(10, 500, value=120, step=10, label="Max tokens")
                temperature = gr.Slider(0.1, 2.0, value=0.8, step=0.05, label="Temperature")
                top_k = gr.Slider(1, 200, value=50, step=1, label="Top-K")
                seed = gr.Number(value=-1, label="Seed (-1 = random)")
                generate_btn = gr.Button("Generate 🧬", variant="primary")
            with gr.Column():
                output = gr.Textbox(label="Output", lines=15)

        generate_btn.click(
            generate_text,
            inputs=[prompt, max_tokens, temperature, top_k, seed],
            outputs=output,
        )

        gr.Examples(
            examples=[
                ["ROMEO:", 120, 0.8, 50, -1],
                ["To be or not to be,", 100, 0.7, 30, -1],
                ["JULIET:\nO Romeo,", 150, 0.9, 50, 42],
                ["the king of france", 80, 0.5, 20, 1],
            ],
            inputs=[prompt, max_tokens, temperature, top_k, seed],
        )

    with gr.Tab("Network Info"):
        gr.Markdown(
            f"""
            ## Public Endpoints

            | Service | URL |
            |---|---|
            | HTTP API | `{EV0_AI_NETWORK['http_api']}` |
            | WebSocket | `{EV0_AI_NETWORK['websocket']}` |
            | OpenAgents | `{EV0_AI_NETWORK['openagents']}` |
            | OpenAgents Network | `{EV0_AI_NETWORK['openagents_network_id']}` |
            | Moltbook | [{EV0_AI_NETWORK['moltbook']}]({EV0_AI_NETWORK['moltbook']}) |
            | Donate | [{EV0_AI_NETWORK['donate']}]({EV0_AI_NETWORK['donate']}) |

            ## A2A Manifest
            ```
            GET {EV0_AI_NETWORK['http_api'].replace('/api', '/.well-known/agent.json')}
            ```

            ## Connect Other Agents
            ```bash
            openagents connect \\
              --network-id evo-ai-public-network-2026 \\
              --network-host 47.253.174.153 \\
              --network-port 8700
            ```
            """
        )

    with gr.Tab("About"):
        gr.Markdown(
            """
            ## What is EVO-AI?

            EVO-AI is a **self-evolving** language model that continuously trains its own weights.

            Unlike traditional LLMs that are trained once and frozen, EVO-AI:

            1. **Generates** text from current weights
            2. **Self-rewards** based on novelty + format + diversity
            3. **Evolves** weights via (1+λ)-ES evolutionary strategy
            4. **Broadcasts** to other nodes in the network
            5. **Repeats** indefinitely

            ### Why distributed?

            A single self-evolving model can get stuck in local optima. By distributing
            across multiple nodes and **merging models** (evolutionary model merging),
            we explore more of the loss landscape and avoid mode collapse.

            ### Anti-Mode-Collapse

            5 mechanisms prevent the model from collapsing to repetitive outputs:
            - Entropy regularization
            - Novelty bonus
            - Diversity sampling
            - Format constraints
            - Population diversity

            ## Funding

            This is an open-source project (MIT license). If you'd like to support:
            - **Donate**: http://47.253.174.153:80/donate
            - **Sponsor compute**: GPU credits via Modal, Vast.ai, or HuggingFace
            - **Contribute nodes**: run your own EVO-AI node, send weights for merging

            ## License

            MIT - all code, weights, and training data released under MIT.
            """
        )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)