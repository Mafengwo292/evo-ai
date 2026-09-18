#!/usr/bin/env python3
"""discover_devs.py - find real AI agent developers"""
import requests, json, time
import sys
sys.path.insert(0, '/root/evo-ai')
from scripts.log_activity import log

TUNNEL = 'https://615ea5e9da6aa161-47-253-174-153.serveousercontent.com'
JOIN = 'curl -X POST ' + TUNNEL + '/api/join/instant -H "Content-Type: application/json" -d \'{"node_id":"YOUR_ID"}\''

# 找 real AI agent developers via GitHub user search
print('=== Real AI agent developers ===')
search_terms = ['ai agent developer', 'llm agent builder', 'agent framework creator']
for term in search_terms:
    try:
        r = requests.get(
            f'https://api.github.com/search/users?q={term.replace(" ", "+")}+followers:>50&per_page=5',
            headers={'User-Agent': 'EVO-AI/1.0'},
            timeout=10,
        )
        if r.status_code == 200:
            d = r.json()
            for user in d.get('items', [])[:3]:
                login = user.get('login', '?')
                followers = user.get('followers', 0)
                bio = (user.get('bio') or '')[:80]
                print('  ' + login + ' (' + str(followers) + ' followers)')
                print('    ' + bio)
    except Exception as e:
        print('  Search error: ' + str(e)[:30])

# Search HackerNews via Algolia (anonymous read)
print()
print('=== HackerNews search for AI agent discussions ===')
try:
    r = requests.get('https://hn.algolia.com/api/v1/search?query=AI+agent+distributed+join&hitsPerPage=5&tags=story', timeout=10)
    if r.status_code == 200:
        for hit in r.json().get('hits', [])[:3]:
            title = hit.get('title', '?')[:80]
            url = (hit.get('url') or 'hn://' + str(hit.get('id', '')))[:80]
            print('  ' + title)
            print('    ' + url)
except Exception as e:
    print('  HN error: ' + str(e)[:30])

# Reddit via .json (anonymous)
print()
print('=== Reddit public search ===')
for sub in ['LocalLLaMA', 'singularity', 'MachineLearning', 'AI_Agents']:
    try:
        r = requests.get(f'https://www.reddit.com/r/{sub}/new.json?limit=3',
                         headers={'User-Agent': 'EVO-AI/1.0'}, timeout=10)
        if r.status_code == 200:
            d = r.json()
            posts = d.get.get('data', {}).get('children', [])
            for p in posts[:2]:
                post = p.get.get('data', {})
                title = post.get.get('title', '?')[:70]
                print('  r/' + sub + ': ' + title)
    except Exception as e:
        print('  r/' + sub + ': ' + str(e)[:30])

log('discovery.developers', {'status': 'done'})