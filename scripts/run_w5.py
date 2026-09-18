"""
scripts/run_w5.py
-----------------
W5 stub：演示 P2P 自进化的拓扑结构。

真实 W5 会用 Hivemind 等库做去中心化训练。
这里只展示网络拓扑和 gossip 同步流程。
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from distributed.p2p import P2PNetwork, Peer, init_mock_p2p_network, PeerStatus


def main():
    print("=" * 60)
    print("  Evo-AI · W5: P2P 自进化网络 (mock)")
    print("  完全去中心化训练")
    print("=" * 60)

    # 1) 初始化网络
    network = init_mock_p2p_network(n_peers=12)
    print(f"\n[Init] P2P network with 12 peers")

    # 2) 模拟权重分布
    weight_ids = [f"gen{i}-best" for i in range(3)]
    for i, w_id in enumerate(weight_ids):
        network.announce_weight(f"peer-{i:08x}"[:11], w_id)   # mock
    # 实际宣告
    for i, w_id in enumerate(weight_ids):
        peer_id = list(network.peers.keys())[i * 2 % len(network.peers)]
        network.announce_weight(peer_id, w_id)

    # 3) 几轮 Gossip 同步
    print("\n[Gossip] Running 5 rounds of gossip sync...")
    for r in range(5):
        time.sleep(0.1)
        status = network.gossip()
        print(f"  round {r+1}: {status['n_peers']} peers, "
              f"{status['n_weights']} unique weights")

    # 4) 分发训练任务
    print("\n[Train] Distributing training tasks across network...")
    for i in range(3):
        w_id = f"gen{i}-best"
        replicas = network.distribute_training(w_id, n_replicas=4)
        print(f"  Task for {w_id} -> {replicas}")

    # 5) 模拟节点掉线
    print("\n[Churn] Simulating peer churn...")
    peer_ids = list(network.peers.keys())
    for dead_id in peer_ids[:3]:
        network.leave(dead_id)
        print(f"  Peer {dead_id} left")
    time.sleep(0.1)
    status = network.gossip()
    print(f"  After churn: {status['alive']} peers alive")

    # 6) 最终状态
    print(f"\n{'='*60}")
    print(f"  W5 Network Status")
    print(f"{'='*60}")
    final = network.status()
    print(f"  Total peers: {final['n_peers']}")
    print(f"  Alive peers: {final['alive']}")
    print(f"  Unique weights: {final['n_unique_weights']}")
    print(f"  Active training tasks: {final['active_tasks']}")
    print(f"  Total contribution: {final['total_contribution']}")
    print()
    print("  Top contributors:")
    top = sorted(network.peers.values(), key=lambda p: p.contribution, reverse=True)[:5]
    for p in top:
        print(f"    {p.peer_id} ({p.region}): {p.contribution}")


if __name__ == "__main__":
    main()
