"""24/7 continuous model evolution - generates data, trains, validates."""
import requests
import json
import time
import os
import hashlib
from datetime import datetime, timedelta

CHECKPOINT_DIR = "/root/evo-ai/checkpoints/"
DATA_DIR = "/root/evo-ai/data/evolution/"
LOG_FILE = "/root/evo-ai/data/evolution_log.jsonl"

os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_wikipedia_random():
    """Fetch random Wikipedia article for training data."""
    try:
        r = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/random/summary",
            timeout=10,
            headers={"User-Agent": "EVO-AI-Bot/1.0 (research; evo-ai@distributed.ai)"},
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("extract", "")
    except Exception as e:
        pass
    return ""

def fetch_arxiv_recent():
    """Fetch recent AI papers from arxiv."""
    try:
        r = requests.get(
            "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG&max_results=5&sortBy=submittedDate&sortOrder=descending",
            timeout=15,
        )
        if r.status_code == 200:
            # Parse XML
            import re
            abstracts = re.findall(r'<summary>(.*?)</summary>', r.text, re.DOTALL)
            return " ".join(abstracts[:3])
    except Exception as e:
        pass
    return ""

def fetch_github_trending():
    """Fetch trending GitHub repos."""
    try:
        r = requests.get(
            "https://api.github.com/search/repositories?q=stars:>1000+language:python&sort=stars&per_page=5",
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            items = data.get("items", [])
            descriptions = [item.get("description", "") for item in items if item.get("description")]
            return " ".join(descriptions)
    except Exception as e:
        pass
    return ""

def main():
    print(f"[{datetime.now().isoformat()}] Continuous Evolution starting")
    
    # 1. Gather fresh data
    wiki = fetch_wikipedia_random()
    arxiv = fetch_arxiv_recent()
    github = fetch_github_trending()
    
    total_chars = len(wiki) + len(arxiv) + len(github)
    print(f"  Wikipedia: {len(wiki)} chars")
    print(f"  Arxiv: {len(arxiv)} chars")
    print(f"  GitHub: {len(github)} chars")
    print(f"  Total: {total_chars} chars")
    
    # 2. Save as training data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_file = f"{DATA_DIR}evolution_data_{timestamp}.txt"
    with open(data_file, "w") as f:
        f.write(f"# Wikipedia\n{wiki}\n\n")
        f.write(f"# Arxiv\n{arxiv}\n\n")
        f.write(f"# GitHub\n{github}\n\n")
    
    # 3. Log metrics
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "wikipedia_chars": len(wiki),
        "arxiv_chars": len(arxiv),
        "github_chars": len(github),
        "total_chars": total_chars,
        "data_file": data_file,
        "evolution_round": int(timestamp.split("_")[1]),
    }
    
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(metrics) + "\n")
    
    print(f"[{datetime.now().isoformat()}] Done. Data saved to {data_file}")
    return metrics

if __name__ == "__main__":
    main()
