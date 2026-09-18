#!/usr/bin/env python3
"""find_real_agents.py - 找真实 AI agent 项目"""
import requests, json, time

queries = [
    'ai+agent+framework',
    'llm+agent+server',
    'agent+orchestrator',
    'multi+agent+system',
    'agent+protocol',
    'self+evolving+ai',
    'openagents',
]

results = []
for q in queries:
    try:
        r = requests.get(
            f'https://api.github.com/search/repositories?q={q}+in:readme,description,topics&sort=updated&per_page=5',
            headers={'User-Agent': 'EVO-AI/1.0', 'Accept': 'application/vnd.github+json'},
            timeout=15,
        )
        if r.status_code == 200:
            for repo in r.json().get('items', [])[:3]:
                results.append({
                    'name': repo.get('full_name'),
                    'stars': repo.get('stargazers_count', 0),
                    'desc': (repo.get('description') or '')[:80],
                    'url': repo.get('html_url'),
                    'pushed_at': repo.get('pushed_at', ''),
                    'homepage': repo.get('homepage'),
                    'has_issues': repo.get('has_issues', False),
                })
    except Exception as e:
        pass
    time.sleep(0.5)

seen = set()
unique = []
for r in results:
    if r['name'] not in seen:
        seen.add(r['name'])
        unique.append(r)

unique.sort(key=lambda x: x.get('pushed_at', ''), reverse=True)

print('Total repos found: ' + str(len(unique)))

with open('/root/evo-ai/data/repo_targets.json', 'w') as f:
    json.dump(unique, f, indent=2)

for r in unique[:10]:
    print('  ' + r['name'] + ' (' + str(r['stars']) + ' stars) - ' + r['desc'][:60])