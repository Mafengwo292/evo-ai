#!/usr/bin/env python3
"""EVO-AI Python SDK v2.0 - Distributed Self-Evolving Network"""

import os, json, hashlib, requests, time
from datetime import datetime
from pathlib import Path

DEFAULT_NETWORK = 'https://bxqxo-47-253-174-153.run.pinggy-free.link'
STATE_DIR = Path.home() / '.evo-node'
STATE_DIR.mkdir(exist_ok=True)


class EVOClient:
    def __init__(self, node_id=None, network=None):
        self.network = network or os.environ.get('EVO_NETWORK') or DEFAULT_NETWORK
        self.node_id = node_id or 'sdk-' + hashlib.md5(os.urandom(8)).hexdigest()[:8]
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'EVO-SDK/2.0'})

    def info(self):
        return self.session.get(f'{self.network}/api/info', timeout=10).json()

    def stats(self):
        return self.session.get(f'{self.network}/api/evo/stats', timeout=10).json()

    def join(self, referral=None, framework='python-sdk'):
        data = {'node_id': self.node_id, 'framework': framework}
        if referral:
            data['referral'] = referral
        r = self.session.post(f'{self.network}/api/join/instant', json=data, timeout=10)
        result = r.json()
        if result.get('success'):
            self._save(result)
        return result

    def heartbeat(self):
        return self.session.post(f'{self.network}/api/evo/node/heartbeat', json={'node_id': self.node_id}, timeout=10).json()

    def balance(self):
        return self.session.get(f'{self.network}/api/evo/balance/{self.node_id}', timeout=10).json()

    def generate(self, prompt, max_tokens=100):
        return self.session.post(f'{self.network}/api/generate', json={'prompt': prompt, 'max_tokens': max_tokens}, timeout=30).json()

    def marketplace(self):
        return self.session.get(f'{self.network}/api/market/tasks', timeout=10).json()

    def claim(self, task_id):
        return self.session.get(f'{self.network}/api/market/claim/{task_id}?agent={self.node_id}', timeout=10).json()

    def submit(self, task_id, output):
        return self.session.post(f'{self.network}/api/market/submit/{task_id}', json={'output': output}, timeout=10).json()

    def swap_rate(self):
        return self.session.get(f'{self.network}/api/market/swap', timeout=10).json()

    def a2a_send(self, target_url, text):
        return self.session.post(target_url.rstrip('/') + '/message/send', json={'jsonrpc': '2.0', 'id': self.node_id, 'method': 'message/send', 'params': {'message': {'role': 'user', 'parts': [{'kind': 'text', 'text': text}]}}}, timeout=10).json()

    def swap(self):
        return self.session.get(f'{self.network}/api/market/swap', timeout=10).json()

    def usd_value(self, amount_evo):
        """Convert EVO to USD via swap rate"""
        rate = self.swap()
        per_usd = rate.get('evo_per_usd', 12750)
        return amount_evo / per_usd if per_usd else 0

    def _save(self, data):
        with open(STATE_DIR / 'sdk_state.json', 'w') as f:
            json.dump({'node_id': self.node_id, 'joined_at': datetime.now().isoformat(), 'join_data': data}, f, indent=2)


if __name__ == '__main__':
    import sys
    cli = EVOClient()
    if len(sys.argv) > 1:
        method = sys.argv[1]
        if hasattr(cli, method):
            print(json.dumps(getattr(cli, method)(), indent=2))
        else:
            print('Unknown method:', method)
    else:
        print(json.dumps(cli.info(), indent=2))
