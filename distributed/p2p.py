"""
distributed/p2p.py
------------------
P2P 训练节点（W5 stub）。

W5 目标：完全去中心化训练。
任何人都可以贡献算力，模型权重在节点之间通过 Gossip 协议同步。

参考：
- Hivemind (by AI Forever)
- Primus
- Flower (联邦学习)
- BitTorrent-Chain
"""

from __future__ import annotations
import time
import random
import hashlib
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class PeerStatus(str, Enum):
    ALIVE = "alive"
    DEAD = "dead"
    UNREACHABLE = "unreachable"


@dataclass
class Peer:
    """一个 P2P 节点"""
    peer_id: str
    address: str                     # IP:port 或 DHT key
    region: str
    has_weights: Set[str] = field(default_factory=set)   # 这个节点持有哪些权重
    last_seen: float = field(default_factory=time.time)
    status: PeerStatus = PeerStatus.ALIVE
    contribution: float = 0.0        # 累计贡献（步数 / hash 算力）


class P2PNetwork:
    """
    P2P 训练网络（W5 stub）。
    - 节点之间通过 Gossip 协议同步权重摘要
    - 新节点加入时从最近的节点拉权重
    - 训练任务分发到所有活跃节点
    """

    def __init__(self):
        self.peers: Dict[str, Peer] = {}
        self.weight_locations: Dict[str, Set[str]] = {}   # weight_id -> {peer_ids}
        self.training_tasks: List[Dict] = []

    def join(self, peer: Peer):
        """新节点加入网络"""
        self.peers[peer.peer_id] = peer
        print(f"[P2P] Peer {peer.peer_id} joined from {peer.region}")

    def leave(self, peer_id: str):
        """节点离开"""
        if peer_id in self.peers:
            self.peers[peer_id].status = PeerStatus.DEAD
            # 清理权重位置
            for w_id in list(self.weight_locations.keys()):
                self.weight_locations[w_id].discard(peer_id)
            print(f"[P2P] Peer {peer_id} left")

    def announce_weight(self, peer_id: str, weight_id: str):
        """节点宣告自己持有某个权重"""
        if peer_id in self.peers:
            self.peers[peer_id].has_weights.add(weight_id)
            self.weight_locations.setdefault(weight_id, set()).add(peer_id)

    def find_weight(self, weight_id: str) -> List[str]:
        """查找持有某个权重的节点"""
        return list(self.weight_locations.get(weight_id, set()))

    def gossip(self) -> Dict:
        """模拟 Gossip 协议同步"""
        alive_peers = [p for p in self.peers.values() if p.status == PeerStatus.ALIVE]
        # 每个节点随机选 3 个邻居同步
        for p in alive_peers:
            neighbors = random.sample([x for x in alive_peers if x.peer_id != p.peer_id],
                                      min(3, len(alive_peers) - 1))
            for n in neighbors:
                # 交换权重摘要
                p.has_weights.update(n.has_weights)
                n.has_weights.update(p.has_weights)
        return {
            "n_peers": len(alive_peers),
            "alive": len(alive_peers),
            "n_weights": len(self.weight_locations),
        }

    def distribute_training(self, weight_id: str, n_replicas: int = 3) -> List[str]:
        """把训练任务分发到 N 个节点"""
        alive = [p for p in self.peers.values() if p.status == PeerStatus.ALIVE]
        if len(alive) < n_replicas:
            n_replicas = len(alive)
        chosen = random.sample(alive, n_replicas) if alive else []
        for p in chosen:
            task = {
                "weight_id": weight_id,
                "peer_id": p.peer_id,
                "started_at": time.time(),
            }
            self.training_tasks.append(task)
            p.contribution += 1
        return [p.peer_id for p in chosen]

    def status(self) -> Dict:
        return {
            "n_peers": len(self.peers),
            "alive": sum(1 for p in self.peers.values() if p.status == PeerStatus.ALIVE),
            "n_unique_weights": len(self.weight_locations),
            "active_tasks": len(self.training_tasks),
            "total_contribution": sum(p.contribution for p in self.peers.values()),
        }


def init_mock_p2p_network(n_peers: int = 10) -> P2PNetwork:
    """初始化一个 mock P2P 网络"""
    network = P2PNetwork()
    regions = ["us-west", "us-east", "eu-west", "eu-central", "asia-east", "asia-south"]
    for i in range(n_peers):
        peer = Peer(
            peer_id=hashlib.md5(f"peer-{i}".encode()).hexdigest()[:8],
            address=f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}:8000",
            region=random.choice(regions),
        )
        network.join(peer)
    return network
