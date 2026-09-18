"""
scripts/run_all.py
------------------
端到端自进化流水线：W1 + W2 + W3 串起来跑。

完整流程：
1. W1 阶段：在本地（mock）训练一个初始模型
2. W2 阶段：把种群调度到云端（mock）跑分布式训练
3. W3 阶段：用自生成数据循环让种群进化
4. 总结：输出最终最优个体 + 完整进化历史

用法：
  python scripts/run_all.py
"""

import sys
import os
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evolution.data_generator import DataGenerator
from evolution.self_play import SelfPlayLoop, TrainingBuffer
from distributed.coordinator import DistributedCoordinator
from distributed.fleet import Fleet


def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def run_w1_phase():
    """W1: 训练初始模型"""
    print_header("W1: 从零训练初始模型 (mock)")
    print("  · 自己写 Transformer（gpt.py）")
    print("  · 字符级 tokenizer + Tiny Shakespeare")
    print("  · 训练循环（AdamW + cosine LR + warmup）")

    # mock：模拟训练过程
    base_quality = 0.3
    print(f"\n  训练 2000 步...")
    for step in [0, 500, 1000, 1500, 1999]:
        # 模拟 loss 下降
        loss = 4.17 * (0.55 ** (step / 500))
        print(f"    step {step:5d} | loss {loss:.3f}")
    print(f"\n  ✓ 训练完成，初始模型质量: {base_quality}")
    return base_quality


def run_w2_phase(init_quality):
    """W2: 分布式调度种群"""
    print_header("W2: 跨互联网分布式调度种群 (mock)")
    print("  · Fleet: Modal / Vast / Replicate / RunPod 跨大洲算力")
    print("  · Coordinator: 调度 + 选择 + 变异 + 繁殖")

    # 用 DistributedCoordinator 跑几代种群进化
    coord = DistributedCoordinator(
        population_size=4,
        base_config={"n_layer": 2, "d_model": 64, "n_head": 4, "block_size": 64, "vocab_size": 65},
    )
    # W2 跑 2 代，给 W3 准备好初始种群
    coord.evolve(n_generations=2)

    print(f"\n  ✓ 分布式调度完成，最优个体: {coord.store.get_best().weight_id}")
    return coord


def run_w3_phase(coord):
    """W3: 自生成数据循环"""
    print_header("W3: 自生成数据驱动的自进化")
    print("  · 模型自己造数据")
    print("  · Reward function 筛选高分样本")
    print("  · 加进训练 buffer")
    print("  · 训练下一代")

    # 用 coordinator 里的最优个体作为初始 generator
    best = coord.store.get_best()
    init_quality = 1.0 - (best.metrics.get("final_loss", 2.0) / 4.0)
    print(f"  · 初始 model_quality = {init_quality:.3f}")

    gen = DataGenerator(model_quality=init_quality)
    buffer = TrainingBuffer(max_size=2000)
    loop = SelfPlayLoop(
        data_generator=gen,
        buffer=buffer,
        n_per_prompt=4,
        top_k_ratio=0.5,
    )
    loop.run(n_steps=10)
    return loop


def main():
    print("=" * 60)
    print("  Evo-AI · 端到端自进化大模型")
    print("  从零训练 → 分布式调度 → 自生成数据进化")
    print("=" * 60)

    t0 = time.time()

    # W1
    init_quality = run_w1_phase()
    time.sleep(0.3)

    # W2
    coord = run_w2_phase(init_quality)
    time.sleep(0.3)

    # W3
    loop = run_w3_phase(coord)
    time.sleep(0.3)

    # 总结
    elapsed = time.time() - t0
    print_header("全流程完成")
    print(f"  · 总耗时: {elapsed:.1f}s")
    print(f"  · W2 最终最优 loss: {coord.store.get_best().metrics.get('final_loss'):.4f}")
    print(f"  · W3 最终 model_quality: {loop.gen.model_quality:.3f}")
    print(f"  · W3 buffer 样本数: {loop.buffer.stats()['n']}")
    print()
    print("  接下来可以做：")
    print("    1. 跑 python scripts/run_w2.py --gens 10 --pop 8 真实做分布式")
    print("    2. 跑 python scripts/run_w3.py --steps 30 看更长的自进化曲线")
    print("    3. 跑 python scripts/train_w1.py --steps 2000 真实训练模型")
    print("    4. 部署到 Modal: modal deploy distributed/modal_trainer.py")


if __name__ == "__main__":
    main()
