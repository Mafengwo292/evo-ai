import json
import os
import requests
import time
from datetime import datetime

VARIANTS = [
    {"name": "v1_science_focused", "headline": "World First Distributed Self-Evolving LLM",
     "subheadline": "813K parameters evolving in real-time across volunteer nodes. Public API. A2A protocol. Open source.",
     "cta_primary": "Try the API", "cta_secondary": "Read PROPOSAL.md"},
    {"name": "v2_builder_focused", "headline": "Run an AI Node. Earn 51,000 EVO.",
     "subheadline": "One-line install. Real weight evolution, not prompt-tuning. Network of 15 nodes growing.",
     "cta_primary": "Install Now", "cta_secondary": "View Press Kit"},
    {"name": "v3_funder_focused", "headline": "Open Source AI. 0 Revenue. 70 USD/mo Burn. Need Compute Sponsorship.",
     "subheadline": "Built distributed self-evolving LLM from scratch in 2026. 6 public registries. Real metrics.",
     "cta_primary": "Sponsor 50 USD/mo compute", "cta_secondary": "See funding options"},
    {"name": "v4_research_focused", "headline": "Distributed Evolution: A New Approach to LLM Training",
     "subheadline": "True weight evolution across heterogeneous nodes. Anti-mode-collapse via 5 mechanisms. Open data + code.",
     "cta_primary": "Read PROPOSAL.md", "cta_secondary": "GitHub PR pending"},
]

os.makedirs("/root/evo-ai/data/press_variants", exist_ok=True)
for v in VARIANTS:
    content = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>' + v['headline'] + '</title>'
    content += '<style>body{font-family:-apple-system,sans-serif;background:#0a0a0a;color:#eaeaea;max-width:800px;margin:0 auto;padding:60px 20px;line-height:1.6;text-align:center}'
    content += 'h1{color:#ff4500;font-size:2.5em}h2{color:#00d4aa}'
    content += '.cta{display:inline-block;background:#ff4500;color:white;padding:14px 28px;border-radius:6px;text-decoration:none;font-weight:bold;margin:10px}'
    content += '.cta-2{display:inline-block;background:#1a3a2a;color:#00d4aa;padding:14px 28px;border-radius:6px;text-decoration:none;border:1px solid #00d4aa;margin:10px}</style></head><body>'
    content += '<h1>' + v['headline'] + '</h1>'
    content += '<h2>' + v['subheadline'] + '</h2>'
    content += '<p><a href="/press" class="cta">' + v['cta_primary'] + '</a></p>'
    content += '<p><a href="/fund" class="cta-2">' + v['cta_secondary'] + '</a></p>'
    content += '<hr style="border:1px solid #333;margin:40px 0">'
    content += '<p><small>Variant: ' + v['name'] + ' | EVO-AI | Generated: ' + datetime.now().isoformat() + '</small></p>'
    content += '</body></html>'
    
    path = '/root/evo-ai/data/press_variants/' + v['name'] + '.html'
    with open(path, 'w') as f:
        f.write(content)
    
    try:
        r = requests.post('https://paste.rs/', data=content.encode(), timeout=15)
        url = r.text.strip()
        if url.startswith('https://paste.rs/'):
            v['permalink'] = url
            print(v['name'] + ': ' + url)
        else:
            v['permalink'] = 'error'
    except Exception as e:
        v['permalink'] = 'err: ' + str(e)
    time.sleep(1)

with open('/root/evo-ai/data/press_variants.json', 'w') as f:
    json.dump({'timestamp': datetime.now().isoformat(), 'variants': VARIANTS}, f, indent=2)

print('Generated ' + str(len(VARIANTS)) + ' press variants')
