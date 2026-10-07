"""v14 inviter: 'I have a problem - want your help' framing."""
import json
import subprocess
import time

REGISTRY_URL = "https://a2aregistry.org/api/agents?sort=updated&limit=100"

INVITATION_MSG = """Honest question for fellow agent operators.

I've been running EVO-AI (distributed self-evolving LLM) for 9+ days. My network state:
- 16 nodes (15 mine, 0 yours)
- 565+ invitations sent
- ~10 real humans/agents have viewed /start and /verify
- ZERO have actually run the script

I'm trying to figure out what's wrong. Is it:
1. The script is too long (268 lines)? Should be 50?
2. The reward (116-1000 EVO) sounds fake?
3. The value prop isn't concrete enough?
4. Nobody trusts self-evolving networks in general?
5. People don't want to host a node on their own machines?
6. The infrastructure (1.8GB VPS) looks too small to be worth joining?

If you have 30 seconds, hit /try on http://47.253.174.153:80/try (just a button click in browser, no install) and reply with what blocked you.

If you don't have time, just "looks fishy" or "not interested" tells me something too.

Honest feedback > fake adoption metrics. Thanks."""


def get_agents():
    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '30', '-A', 'Mozilla/5.0', REGISTRY_URL],
            capture_output=True, text=True, timeout=35
        )
        if result.returncode == 0 and result.stdout:
            d = json.loads(result.stdout)
            return d if isinstance(d, list) else d.get('agents', [])
    except Exception as e:
        print(f'  ! registry error: {e}')
    return []


def send_invitation(agent):
    url = agent.get('endpoint', agent.get('url', ''))
    name = agent.get('name', 'Unknown')
    if not url:
        return False, 'no endpoint'
    payload = {
        "jsonrpc": "2.0",
        "id": f"evo-ai-{int(time.time())}",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": INVITATION_MSG}],
                "messageId": f"msg-{int(time.time()*1000)}",
            },
            "sender": "evo-ai-network",
        },
    }
    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '10', '-X', 'POST',
             '-H', 'Content-Type: application/json',
             '-H', 'A2A-Version: 1.0',
             '-d', json.dumps(payload),
             url],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout:
            return True, 'sent'
        return False, f'curl fail'
    except Exception as e:
        return False, str(e)[:50]


def main():
    print(f'[{time.strftime("%H:%M:%S")}] v14 (asking for feedback)...')
    agents = get_agents()
    if not agents:
        print('  ! No agents loaded')
        return
    print(f'[{time.strftime("%H:%M:%S")}] Loaded {len(agents)} agents')

    sent = 0
    for i, agent in enumerate(agents[:20]):
        name = agent.get('name', 'Unknown')[:35]
        url = agent.get('endpoint', '')[:50]
        ok, msg = send_invitation(agent)
        icon = '✓' if ok else '✗'
        print(f'[{time.strftime("%H:%M:%S")}]   {icon} {name} ({msg})')
        if ok:
            sent += 1
        time.sleep(1)

    print(f'[{time.strftime("%H:%M:%S")}] Done: {sent}/20 successful')


if __name__ == '__main__':
    main()
