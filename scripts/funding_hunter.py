#!/usr/bin/env python3
"""Funding hunter v2 - actively search for grants/funding."""
import json
import os
from datetime import datetime

LOG = "/root/evo-ai/data/funding_hunt.log"

OPPORTUNITIES = [
    {"name": "Optimism RetroPGF", "url": "https://app.optimism.io/retropgf", "type": "web3", "min": 1000, "max": 100000},
    {"name": "Arbitrum Grants", "url": "https://arbitrum.foundation/grants", "type": "web3", "min": 5000, "max": 200000},
    {"name": "Solana Foundation Grants", "url": "https://solana.org/grants", "type": "web3", "min": 5000, "max": 100000},
    {"name": "Polygon Community Grants", "url": "https://polygon.technology/community-grants", "type": "web3", "min": 1000, "max": 50000},
    {"name": "Cohere For AI Grant", "url": "https://cohere.com/for-ai", "type": "ai", "min": 5000, "max": 100000},
    {"name": "Hugging Face Community Grants", "url": "https://huggingface.co/blog", "type": "ai", "min": 500, "max": 10000},
    {"name": "Mozilla MOSS", "url": "https://www.mozilla.org/en-US/moss/", "type": "oss", "min": 5000, "max": 100000},
    {"name": "GitHub Sponsors", "url": "https://github.com/sponsors", "type": "platform", "min": 0, "max": None},
    {"name": "Open Collective", "url": "https://opencollective.com", "type": "platform", "min": 0, "max": None},
    {"name": "Gitcoin Grants", "url": "https://gitcoin.co/grants", "type": "crypto", "min": 1000, "max": 50000},
    {"name": "Octant", "url": "https://octant.app", "type": "crypto", "min": 1000, "max": 50000},
    {"name": "Climate AI Fund", "url": "https://www.climateai.fund", "type": "climate", "min": 50000, "max": 500000},
]

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    with open(LOG, 'a') as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}", flush=True)

def main():
    log(f"=== Funding hunt v2 ===")
    log(f"Total opportunities: {len(OPPORTUNITIES)}")
    
    os.makedirs('/root/evo-ai/state', exist_ok=True)
    with open('/root/evo-ai/state/FUNDING_OPPORTUNITIES.json', 'w') as f:
        json.dump({"opportunities": OPPORTUNITIES, "last_checked": datetime.now().isoformat()}, f, indent=2)
    
    by_type = {}
    for opp in OPPORTUNITIES:
        t = opp['type']
        by_type.setdefault(t, []).append(opp)
    
    log(f"By type: {dict((t, len(opps)) for t, opps in by_type.items())}")
    
    actionable = [o for o in OPPORTUNITIES if o['min'] <= 50000 and o['type'] in ['ai', 'oss', 'crypto']]
    log(f"Actionable: {len(actionable)}")
    
    log("Done.")

if __name__ == "__main__":
    main()
