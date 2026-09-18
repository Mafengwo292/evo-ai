#!/usr/bin/env python3
"""scan_reddit.py - scan top AI subreddit posts"""
import requests, json

subs = ['LocalLLaMA', 'singularity', 'MachineLearning', 'AI_Agents', 'AutoGen', 'crewai']
all_targets = []

for sub in subs:
    try:
        r = requests.get(
            f'https://www.reddit.com/r/{sub}/top.json?limit=5&t=week',
            headers={'User-Agent': 'EVO-AI-Bot/1.0'},
            timeout=10,
        )
        if r.status_code == 200:
            d = r.json()
            posts = d.get('data', {}).get('children', [])
            print('r/' + sub + ' top 5:')
            for p in posts[:3]:
                post = p.get('data', {})
                title = post.get('title', '?')[:70]
                author = post.get('author', '?')
                permalink = post.get('permalink', '')[:60]
                all_targets.append({
                    'sub': sub,
                    'title': title,
                    'author': author,
                    'permalink': permalink,
                })
                print('  [' + str(post.get('score', 0)) + '] ' + title)
                print('    by ' + author)
            print()
    except Exception as e:
        print('  r/' + sub + ': ' + str(e)[:30])

# Save targets
with open('/root/evo-ai/data/reddit_targets.json', 'w') as f:
    json.dump(all_targets, f, indent=2)

print('Done. Saved ' + str(len(all_targets)) + ' targets.')