"""
scripts/run_w3.py
-----------------
W3 启动入口：自生成数据驱动的自进化。

跑这个会：
1. 启动一个初始模型（mock，质量 0.3）
2. 跑 N 步自生成数据循环
3. 每一步：模型生成 → reward 评估 → 选 top K → 加入 buffer → 模拟训练 → 模型质量提升
4. 打印进化曲线

用法：
  python scripts/run_w3.py --steps 15
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evolution.data_generator import DataGenerator
from evolution.self_play import SelfPlayLoop, TrainingBuffer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=12, help="自进化步数")
    parser.add_argument("--n_per_prompt", type=int, default=4)
    parser.add_argument("--init_quality", type=float, default=0.3)
    parser.add_argument("--top_k", type=float, default=0.5, help="选 top K 比例")
    args = parser.parse_args()

    # 1) 初始模型（mock，质量 0.3，模拟"刚训练完的弱模型"）
    gen = DataGenerator(model_quality=args.init_quality)
    buffer = TrainingBuffer(max_size=2000)

    # 2) 自进化循环
    loop = SelfPlayLoop(
        data_generator=gen,
        buffer=buffer,
        n_per_prompt=args.n_per_prompt,
        top_k_ratio=args.top_k,
    )

    # 3) 跑
    history = loop.run(n_steps=args.steps)

    # 4) 展示最优样本
    print(f"\n{'='*60}")
    print(f"  Top Samples (highest reward)")
    print(f"{'='*60}")
    top = buffer.get_training_texts(top_k=3)
    for i, t in enumerate(top, 1):
        print(f"\n[Sample {i}] (reward={heuristic_reward_local(t):.3f})")
        print("-" * 40)
        print(t[:300])
        print("...")


def heuristic_reward_local(text):
    # 局部 import 避免循环
    from evolution.reward import heuristic_reward
    return heuristic_reward(text)


if __name__ == "__main__":
    main()
