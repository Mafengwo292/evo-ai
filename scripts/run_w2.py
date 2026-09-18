"""
scripts/run_w2.py
-----------------
W2 启动入口：分布式自进化 demo。

跑这个脚本会：
1. 创建一个跨互联网的 mock 算力集群（Modal / Vast / Replicate / RunPod）
2. 初始化一个模型种群（4 个个体）
3. 跑 N 代进化：
   - 调度训练任务到云端 GPU（mock）
   - 训练完推送到 WeightStore
   - 评估 + 选择 + 变异
4. 输出最终最优个体

用法：
  python scripts/run_w2.py --gens 5 --pop 4
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from distributed.coordinator import DistributedCoordinator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gens", type=int, default=3, help="进化代数")
    parser.add_argument("--pop", type=int, default=4, help="种群大小")
    parser.add_argument("--config_layer", type=int, default=2)
    parser.add_argument("--config_dmodel", type=int, default=64)
    args = parser.parse_args()

    base_config = {
        "n_layer": args.config_layer,
        "d_model": args.config_dmodel,
        "n_head": 4,
        "block_size": 64,
        "vocab_size": 65,
    }

    coordinator = DistributedCoordinator(
        population_size=args.pop,
        base_config=base_config,
    )

    coordinator.evolve(n_generations=args.gens)


if __name__ == "__main__":
    main()
