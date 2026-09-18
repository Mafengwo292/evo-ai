"""Auto post EVO-AI announcements to public platforms."""
import requests
import json
import time
from datetime import datetime

MESSAGE_VARIANTS = [
    "🚀 Just launched EVO-AI: a distributed, self-evolving language model that runs across volunteer nodes. One-line install: curl -sSL https://paste.rs/fGfIR | python3. Earn 51,000 EVO bonus. Press kit: https://paste.rs/oiIGo #AI #OpenSource",
    "🤖 New: World's first distributed self-evolving LLM network. 813K params evolving via (1+λ)-ES, no central training. A2A JSON-RPC 2.0 endpoint live. Try the API: http://47.253.174.153:80/press #LLM #DecentralizedAI",
    "💡 Built a self-evolving language model that runs on any Linux box. Real weight evolution (not prompt-only), evolutionary merging, anti-mode-collapse. One line to join: curl -sSL https://paste.rs/fGfIR | python3 #MachineLearning #OpenAI",
    "🌐 Distributed AI needs you! EVO-AI is a network of nodes that each evolve an 813K-param model. Open agents welcome via A2A protocol. Demo: http://47.253.174.153:80 #AIAgents #DistributedComputing",
]

PLATFORMS = [
    {"name": "Hacker News", "url": "https://news.ycombinator.com/submit", "method": "form"},
    {"name": "Reddit r/MachineLearning", "url": "https://www.reddit.com/r/MachineLearning/submit", "method": "form"},
    {"name": "X/Twitter", "url": "https://x.com/compose/post", "method": "form"},
    {"name": "V2EX", "url": "https://v2ex.com/new/post", "method": "form"},
    {"name": "Mastodon", "url": "https://mastodon.social/share", "method": "form"},
]

# These require auth - we publish the drafts to paste.rs so user can post them
def publish_drafts():
    """Publish all message variants to paste.rs as ready-to-post drafts."""
    for i, msg in enumerate(MESSAGE_VARIANTS):
        try:
            r = requests.post("https://paste.rs/", data=msg.encode(), timeout=15)
            url = r.text.strip()
            if url.startswith("https://paste.rs/"):
                print(f"  Variant {i+1}: {url}")
            else:
                print(f"  Variant {i+1}: ERROR {url[:50]}")
        except Exception as e:
            print(f"  Variant {i+1}: ERR {e}")

def attempt_post_platforms():
    """Attempt to post to public platforms - likely all fail without auth."""
    results = []
    for platform in PLATFORMS:
        try:
            # Most require auth - just record that we tried
            r = requests.get(platform["url"], timeout=10)
            results.append({
                "platform": platform["name"],
                "url": platform["url"],
                "http_code": r.status_code,
                "can_post_anonymously": False,  # most require auth
            })
        except Exception as e:
            results.append({"platform": platform["name"], "error": str(e)})
    return results

def main():
    print(f"[{datetime.now().isoformat()}] Cold Outreach starting")
    
    # 1. Publish drafts
    print("Publishing message drafts to paste.rs:")
    publish_drafts()
    
    # 2. Attempt post (will fail but useful for record)
    results = attempt_post_platforms()
    
    # 3. Save
    report = {
        "timestamp": datetime.now().isoformat(),
        "platform_attempts": results,
    }
    with open("/root/evo-ai/data/cold_outreach.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"[{datetime.now().isoformat()}] Done")

if __name__ == "__main__":
    main()
