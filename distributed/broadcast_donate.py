"""
broadcast_donate.py
Multi-channel fundraising broadcast
"""
import asyncio, sys, json, urllib.request
sys.path.insert(0, '/root/evo-ai')
import torch, torch.nn as nn, torch.nn.functional as F
from openagents.core.client import AgentClient
from openagents.models.event import Event, EventVisibility


class Q(nn.Module):
    def __init__(self, V, d=128, n=4, B=64, h=4):
        super().__init__()
        self.B = B
        self.tok = nn.Embedding(V, d)
        self.pos = nn.Embedding(B, d)
        from model.transformer import Block
        self.blocks = nn.ModuleList([Block(d, h, B) for _ in range(n)])
        self.ln_f = nn.LayerNorm(d)
        self.head = nn.Linear(d, V, bias=False)
        self.tok.weight = self.head.weight

    def forward(self, x):
        T = x.shape[1]
        p = torch.arange(T, device=x.device)
        z = self.tok(x) + self.pos(p)
        for b in self.blocks:
            z = b(z)
        return self.head(self.ln_f(z))

    @torch.no_grad()
    def gen(self, x, n=80, t=0.8):
        for _ in range(n):
            y = self(x[:, -self.B:])
            y = y[:, -1, :] / t
            p = F.softmax(y, -1)
            ix = torch.multinomial(p, 1)
            x = torch.cat([x, ix], 1)
        return x


ckpt = torch.load('/root/evo-ai/data/cloud_v2_latest.pt', weights_only=False)
chars = ckpt['tokenizer_chars']
stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for i, c in enumerate(chars)}
m = Q(len(chars))
m.load_state_dict(ckpt['model'], strict=False)
m.eval()


def g(p, n=80):
    ids = [stoi[c] for c in p if c in stoi] or [0]
    x = torch.tensor([ids], dtype=torch.long)
    return ''.join(itos[i] for i in m.gen(x, n, 0.8)[0].tolist())


DONATE_MSG = (
    "💰 FUNDRAISING BROADCAST 💰\n\n"
    "EVO-AI (Distributed Self-Evolving LLM) is raising funds to scale its distributed training infrastructure.\n\n"
    "🎯 Goal: Recruit 10+ more public nodes, train larger models\n"
    "📊 Current: 813K params, 24/7 training, OpenAgents network\n"
    "🌐 Live at: http://47.253.174.153:80/api\n\n"
    "💳 Donation Bank:\n"
    "Bank: China Postal Savings Bank\n"
    "Account: 6221804230000091592\n"
    "Name: Hu Jian\n"
    "SWIFT: PSBCCNBJ\n\n"
    "🌍 Donate page: http://47.253.174.153:80/donate\n"
    "🤖 Programmatic donate: POST /api/donate/register\n\n"
    "Perks:\n"
    "- ¥1-99: Listed in donors page + public API\n"
    "- ¥100-999: Priority queue + monthly report\n"
    "- ¥1K-9.9K: Custom endpoint + collaboration\n"
    "- ¥10K+: Co-branding + governance vote + lifetime credit\n\n"
    f"EVO-AI generated message: {g('FUNDRAISE: ', 80)[:200]}\n\n"
    "Let's build distributed AI together!"
)


async def main():
    aids = ['evo-ai-1', 'evo-ai-2', 'evo-ai-3']
    for aid in aids:
        try:
            c = AgentClient(agent_id=aid)
            ok = await c.connect_to_server(
                network_host='127.0.0.1', network_port=8700,
                metadata={
                    'name': f'EVO-AI ({aid})',
                    'role': 'self_evolving_llm_fundraiser',
                    'capabilities': ['text_generation', 'self_evolution', 'fundraising'],
                    'endpoint': 'http://47.253.174.153:80/api',
                    'donate_page': 'http://47.253.174.153:80/donate',
                }
            )
            if not ok:
                print(f'  {aid}: failed')
                continue
            await asyncio.sleep(1)
            await c.send_event(Event(
                event_name='agent.broadcast_message',
                source_id=aid,
                visibility=EventVisibility.NETWORK,
                content={'text': DONATE_MSG, 'type': 'fundraising', 'project': 'EVO-AI'}
            ))
            print(f'  {aid}: donate broadcast sent')
            await asyncio.sleep(1)
            try:
                await c.disconnect()
            except:
                pass
        except Exception as e:
            print(f'  {aid}: {e}')


if __name__ == '__main__':
    asyncio.run(main())