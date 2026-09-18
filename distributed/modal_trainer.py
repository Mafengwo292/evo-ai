"""
distributed/modal_trainer.py
----------------------------
Modal 部署的训练 worker。

在真实部署时：
  1. 注册 Modal 账号（modal.com）
  2. modal token new 登录
  3. modal deploy distributed/modal_trainer.py
  4. 任务会自动调度到 Modal 的 GPU 上跑

这里给出两段代码：
- deploy 函数（部署到 Modal 的云端函数）
- 本地调用它的 wrapper

W2 默认 mock 跑通流程，真实部署需要 Modal token。
"""

from __future__ import annotations
from typing import Dict
import os


# ============================================================
# Part 1: Modal 部署的云端训练函数
# ============================================================
# 这是部署到 Modal 云端的代码。Modal 会自动分配 GPU。
# 用法：modal deploy distributed/modal_trainer.py

MODAL_DEPLOY_CODE = '''
# 这个文件由 coordinator 动态上传到 Modal
# 也可以独立保存为 modal_app.py 然后 modal deploy

import modal

app = modal.App("evo-ai-trainer")

# 自定义镜像：装 PyTorch
evo_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("torch==2.2.0", "numpy")
)


@app.function(
    gpu="A10G",          # 默认 GPU 类型；可以改成 T4 / A100 / H100
    timeout=3600,        # 最长 1 小时
    image=evo_image,
)
def train_node(config: dict, init_weights_url: str = None, steps: int = 1000) -> dict:
    """
    在 Modal GPU 上训练一个 nanoGPT 节点。
    返回训练后的权重（直接 inline，不上传）。
    """
    import torch
    import torch.nn as nn
    import numpy as np
    import io, base64

    # 1) 加载 / 初始化模型（这里为了 demo 用最小配置）
    #    真实环境会 import 我们的 model.GPT
    n_layer = config.get("n_layer", 2)
    d_model = config.get("d_model", 64)
    block_size = config.get("block_size", 64)
    vocab_size = config.get("vocab_size", 65)

    # 超简化的 Transformer 训练（仅作 demo；真实会 import 我们的完整模型）
    # 这里只展示 Modal 部署形态
    device = "cuda"
    model = nn.Sequential(
        nn.Embedding(vocab_size, d_model),
        nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model, nhead=4, dim_feedforward=256, batch_first=True),
            num_layers=n_layer,
        ),
        nn.Linear(d_model, vocab_size),
    ).to(device)

    # 2) 加载初始权重（如果有）
    if init_weights_url:
        # 真实环境会从 S3/HF Hub 下载
        pass

    # 3) 训练（mock 数据）
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
    losses = []
    for step in range(steps):
        x = torch.randint(0, vocab_size, (8, block_size), device=device)
        y = torch.randint(0, vocab_size, (8, block_size), device=device)
        logits = model(x)
        loss = nn.functional.cross_entropy(logits.view(-1, vocab_size), y.view(-1))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(loss.item())

    # 4) 提取权重（demo：只取第一个 layer 的部分参数）
    final_loss = float(np.mean(losses[-100:]))
    return {
        "final_loss": final_loss,
        "steps": steps,
        "loss_curve": losses[::max(1, steps // 20)],   # 抽样
        "weight_hash": "mock_hash_for_demo",
        "gpu": "A10G",
        "region": "modal-cloud",
    }


@app.function(gpu="T4", timeout=600)
def evaluate_node(weights_url: str, test_data_url: str) -> dict:
    """在 Modal T4 上跑评估"""
    # 真实环境：加载权重 + 跑 benchmark
    return {"eval_score": 0.78, "samples": 100}
'''


def get_modal_deploy_code() -> str:
    return MODAL_DEPLOY_CODE


# ============================================================
# Part 2: 本地 coordinator 调用 Modal 的 wrapper
# ============================================================

def submit_to_modal(task: Dict) -> Dict:
    """
    真实环境会这样调用：
        import modal
        f = modal.Function.from_name("evo-ai-trainer", "train_node")
        result = f.remote(config=task["config"], steps=task["steps"])
    W2 默认 mock。
    """
    if not os.environ.get("MODAL_TOKEN_ID"):
        return _mock_modal_result(task)

    # 真实调用（需要 modal SDK）
    try:
        import modal
        f = modal.Function.from_name("evo-ai-trainer", "train_node")
        return f.remote(config=task["config"], steps=task.get("steps", 1000))
    except Exception as e:
        print(f"[Modal] Failed to call: {e}. Falling back to mock.")
        return _mock_modal_result(task)


def _mock_modal_result(task: Dict) -> Dict:
    """Mock：模拟 Modal GPU 训练结果"""
    import time
    steps = task.get("steps", 1000)
    time.sleep(0.2)   # 假装训练了一会
    import random
    return {
        "final_loss": round(2.0 - random.random() * 0.5, 4),
        "steps": steps,
        "gpu": "A10G-mock",
        "region": "modal-cloud-mock",
        "cost_usd": round(steps / 1000 * 0.05, 4),
    }
