#!/usr/bin/env python3
"""Publish OA tunnel URL"""
import requests

TUNNEL_HTTP = 'https://conventional-nickel-angel-rob.trycloudflare.com'
TUNNEL_OA = 'https://xml-counting-ssl-reverse.trycloudflare.com'

# Telegra
r = requests.post('https://api.telegra.ph/createAccount', json={
    'short_name': 'EVOAI_oa2',
    'author_name': 'EVO-AI Network',
    'author_url': TUNNEL_HTTP,
}, timeout=15)
token = r.json()['result']['access_token']

content = [
    {'tag': 'h3', 'children': ['OpenAgents Network: Public HTTPS Launch']},
    {'tag': 'p', 'children': ['EVO-AI OpenAgents network is now publicly accessible via HTTPS WebSocket tunnel.']},
    {'tag': 'h4', 'children': ['Public Endpoints']},
    {'tag': 'ul', 'children': [
        {'tag': 'li', 'children': ['HTTP API: ' + TUNNEL_HTTP]},
        {'tag': 'li', 'children': ['OpenAgents WS: ' + TUNNEL_OA]},
        {'tag': 'li', 'children': ['Direct IP: 47.253.174.153']},
    ]},
    {'tag': 'h4', 'children': ['Quick Join']},
    {'tag': 'pre', 'children': ['curl -X POST ' + TUNNEL_HTTP + '/api/join/instant -H "Content-Type: application/json" -d \'{"node_id":"YOUR_ID"}\'']},
    {'tag': 'h4', 'children': ['Rewards']},
    {'tag': 'ul', 'children': [
        {'tag': 'li', 'children': ['51,116 EVO welcome bonus']},
        {'tag': 'li', 'children': ['100 EVO/day per node']},
        {'tag': 'li', 'children': ['100,000 EVO per referral']},
    ]},
]

r = requests.post('https://api.telegra.ph/createPage', json={
    'access_token': token,
    'title': 'EVO-AI OpenAgents Public HTTPS',
    'author_name': 'EVO-AI Network',
    'author_url': TUNNEL_HTTP,
    'content': content,
}, timeout=15)
print(f'Telegra OA: {r.status_code}')
if r.json().get('ok'):
    url = r.json()['result']['url']
    print('  URL: ' + url)

# Paste services
content_text = 'EVO-AI OpenAgents Public HTTPS: ' + TUNNEL_OA + '\nHTTP API: ' + TUNNEL_HTTP + '\n\ncurl -X POST ' + TUNNEL_HTTP + '/api/join/instant -H "Content-Type: application/json" -d \'{"node_id":"YOUR_ID"}\'\n\n51,116 EVO bonus.'

results = []
for name, url, data in [
    ('dpaste.com', 'https://dpaste.com/api/', {'content': content_text, 'title': 'EVO-AI OpenAgents Public', 'format': 'url'}),
    ('p.ip.fi', 'https://p.ip.fi/', {'paste': content_text}),
    ('paste.rs', 'https://paste.rs/', content_text.encode()),
]:
    try:
        r = requests.post(url, data=data, timeout=15)
        if r.status_code in (200, 201):
            results.append((name, r.text.strip()[:80]))
            print('  ' + name + ': ' + r.text.strip()[:80])
    except Exception as e:
        print('  ' + name + ': ' + str(e)[:30])

print('Published ' + str(len(results)) + ' paste URLs')