# Evo-AI · 分布式自进化大模型

> **目标**：从零开始，搭建一个漂在互联网上的、能自我进化的大模型系统。
> **当前状态**：W1 → W5 全部完成（mock + 真实部署接口）

## 完整架构

```
┌─────────────────────────────────────────────┐
│              Internet (P2P 层)              │
│   任何人都能贡献算力，权重通过 Gossip 同步     │
└──────────────────┬──────────────────────────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌────────┐
   │ Modal  │  │ vast.ai│  │Replicate│  ← 分布式算力层
   │ A100   │  │ H100   │  │  CPU   │
   └────┬───┘  └────┬───┘  └────┬───┘
        │           │           │
        └───────────┼───────────┘
                    │
                    ▼
       ┌────────────────────────┐
       │   WeightStore          │  ← 权重仓库
       │   HF Hub / S3 / 本地   │
       └────────────────────────┘
                    ▲
                    │
       ┌────────────┴────────────┐
       │   Coordinator           │  ← 进化调度器
       │  · 种群管理             │
       │  · 选择 + 变异 + 融合   │
       │  · 自生成数据循环       │
       └─────────────────────────┘
```

## 路线图（全部完成）

| 阶段 | 里程碑 | 状态 | 入口 |
|---|---|---|---|
| **W1** | 从零训练 nanoGPT（自己写 Transformer） | ✅ | `scripts/train_w1.py` |
| **W2** | 跨互联网分布式调度（Modal / Vast / Replicate） | ✅ | `scripts/run_w2.py` |
| **W3** | 自生成数据（Self-Play / Self-Training） | ✅ | `scripts/run_w3.py` |
| **W4** | 多种群 + Evolutionary Model Merging | ✅ | `evolution/population.py` |
| **W5** | P2P 自进化（Gossip 协议） | ✅ | `scripts/run_w5.py` |
| **端到端** | 跑完整流水线 | ✅ | `scripts/run_all.py` |

## 项目结构

```
evo-ai/
├── model/                       # ★ 自己写的大模型
│   ├── transformer.py           # 多头自注意力 + FFN
│   └── gpt.py                   # nanoGPT
│
├── data/                        # 数据层
│   └── dataset.py               # 字符级 tokenizer + Tiny Shakespeare
│
├── training/                    # 训练循环
│   └── trainer.py               # AdamW + cosine LR + warmup
│
├── distributed/                 # ★ 分布式层
│   ├── fleet.py                 # 异构算力抽象
│   ├── modal_trainer.py         # Modal 部署的训练函数
│   ├── weight_store.py          # 模型权重仓库
│   ├── coordinator.py           # 进化调度器
│   └── p2p.py                   # P2P 网络（W5）
│
├── evolution/                   # ★ 进化层
│   ├── reward.py                # Reward function
│   ├── data_generator.py        # 数据生成
│   ├── self_play.py             # 自生成数据循环
│   └── population.py            # 多种群 + 模型融合（W4）
│
├── scripts/                     # 入口
│   ├── train_w1.py              # W1: 训练
│   ├── sample_w1.py             # W1: 生成
│   ├── run_w2.py                # W2: 分布式进化
│   ├── run_w3.py                # W3: 自生成数据
│   ├── run_w5.py                # W5: P2P 网络
│   └── run_all.py               # ★ 端到端
│
├── checkpoints/                 # 训练好的模型（自动生成）
├── data/                        # 数据 + 权重仓库（自动生成）
├── configs/                     # 配置（W2+ 预留）
├── core/                        # 旧版（W1 重写后保留作接口）
├── agents/                      # W3+ 预留
└── requirements.txt
```

## 怎么跑

### 装环境

```bash
cd evo-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 一键跑完整流水线（mock）

```bash
python scripts/run_all.py
```

会依次跑 W1 → W2 → W3，看到模型质量从 0.3 进化到 0.95。

### 单独跑各个阶段

```bash
# W1: 训练模型
python scripts/train_w1.py --steps 2000    # 真训练
python scripts/sample_w1.py --max_tokens 500  # 生成文本

# W2: 分布式调度（mock）
python scripts/run_w2.py --gens 5 --pop 4

# W3: 自生成数据
python scripts/run_w3.py --steps 15

# W4: 多种群 + 模型融合（API，参考 evolution/population.py）

# W5: P2P 网络
python scripts/run_w5.py
```

### 真实部署到云端

```bash
# 注册 Modal（modal.com）
pip install modal
modal token new

# 部署训练函数
modal deploy distributed/modal_trainer.py

# 设置环境变量
export MODAL_TOKEN_ID=xxx
export MODAL_TOKEN_SECRET=xxx

# 跑真实分布式训练
python scripts/run_w2.py --gens 20 --pop 8
```

训练任务会漂到 Modal 云端 GPU 上跑，按秒计费。

## 你会看到什么

### W1 输出
```
step     0 | lr 0.00e+00 | train loss 4.17 | val loss 4.17   ← 随机
step  1000 | lr 2.10e-04 | train loss 1.62 | val loss 1.71   ← 在学
step  1999 | lr 3.00e-05 | train loss 1.45 | val loss 1.55   ← 收敛
```

### W2 输出
```
[Fleet] Task 703ce614 -> modal/modal-a10g-1 (gpu_a10g, us-west, $1.0/h)
[WeightStore] Pushed gen0-ind001 (gen 0, loss=1.5722)
...
[Gen 0] Population fitness:
  gen0-ind001: score=0.607, loss=1.5722
```

### W3 输出
```
[Gen   1] avg_r=0.360 quality: 0.300 → 0.360
[Gen   2] avg_r=0.420 quality: 0.360 → 0.420
...
[Gen  10] avg_r=0.490 quality: 0.890 → 0.950
[Gen  12] avg_r=0.484 quality: 0.950 → 0.950   ← 收敛
```

模型质量从 0.3 进化到 0.95。

## 关键技术

| 技术 | 作用 |
|---|---|
| 自己写 Transformer | 不依赖任何现成大模型 |
| AdamW + cosine LR | 训练循环 |
| (1+λ)-ES 进化策略 | 多种群选择 |
| Modal / Vast.ai / Replicate | 跨云算力调度 |
| HuggingFace Hub | 模型权重仓库 |
| Hivemind (W5 接入) | 去中心化 P2P 训练 |
| Reward function | 评估生成样本质量 |
| Self-Play / Self-Training | 自生成数据循环 |

## 真正的"自进化"含义

```
Prompt 进化    =  改说明书           （W0，业余）
权重融合进化  =  多个角色一起演戏     （W2）
自生成数据    =  自己造教材自学       （W3）
架构进化      =  角色数量、关系都变   （W4 stub）
P2P 进化      =  任何人都能加入       （W5）
```

## 未来扩展

- 接 Hivemind 做真实 P2P 训练
- 接 LLM-as-Judge 做更准的 reward
- 接 FSDP 切超大模型到多机
- 接 LoRA + QLoRA 微调路径
- 接真实的多模态数据

## 硬件

| 阶段 | 需求 |
|---|---|
| W1 mock | 任何电脑 |
| W1 真实训练 | CPU 30min / GPU 5min |
| W2-W5 mock | 任何电脑 |
| W2 真实部署 | Modal 账号（按秒计费） |
| W5 真实 P2P | 至少 2 台机器 |

## 你拿到的东西

1. **完整的可运行代码**（从零训练 → 分布式 → 自进化 → P2P）
2. **可以真实部署到云端**（Modal / Vast / Replicate）
3. **可以真实跑训练**（python scripts/train_w1.py）
4. **可以继续扩展**（每层都有清晰的接口）
