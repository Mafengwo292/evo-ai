"""V2: AI-focused training data collection."""
import requests
import json
import time
import os
import hashlib
from datetime import datetime

DATA_DIR = "/root/evo-ai/data/evolution/"
LOG_FILE = "/root/evo-ai/data/continuous_evolution.log"

os.makedirs(DATA_DIR, exist_ok=True)

# Curated list of AI-relevant Wikipedia articles
WIKI_ARTICLES = [
    "Artificial_intelligence", "Machine_learning", "Deep_learning", 
    "Neural_network", "Transformer_(machine_learning_model)",
    "Large_language_model", "Reinforcement_learning",
    "Evolutionary_algorithm", "Genetic_algorithm", "Distributed_computing",
    "Open_source", "Federated_learning", "Generative_adversarial_network",
    "Natural_language_processing", "Computer_vision",
    "Self-supervised_learning", "Knowledge_distillation",
    "Multi-agent_system", "Agent-based_model", "OpenAI",
    "Python_(programming_language)", "PyTorch", "TensorFlow",
]

def fetch_wiki_article(title):
    """Fetch a specific Wikipedia article."""
    try:
        r = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&explaintext=1&titles={title}",
            timeout=10,
            headers={"User-Agent": "EVO-AI-Bot/2.0 (research; evo-ai@distributed.ai)"},
        )
        if r.status_code == 200:
            d = r.json()
            pages = d['query']['pages']
            return list(pages.values())[0].get('extract', '')
    except Exception as e:
        return ""
    return ""

def fetch_arxiv_recent():
    """Fetch recent AI papers from arxiv."""
    try:
        r = requests.get(
            "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.MA&max_results=10&sortBy=submittedDate&sortOrder=descending",
            timeout=15,
        )
        if r.status_code == 200:
            import re
            text = r.text
            summaries = re.findall(r'<summary>(.*?)</summary>', text, re.DOTALL)
            return " ".join(summaries[:5])
    except:
        pass
    return ""

def fetch_github_trending():
    """Fetch a few GitHub repo descriptions for tech vocabulary."""
    try:
        r = requests.get(
            "https://api.github.com/search/repositories?q=language:python+stars:>1000&sort=stars&per_page=5",
            timeout=15,
            headers={"User-Agent": "EVO-AI-Bot/2.0"},
        )
        if r.status_code == 200:
            d = r.json()
            descriptions = [item.get('description', '') for item in d.get('items', [])[:5] if item.get('description')]
            return " ".join(descriptions)
    except:
        pass
    return ""

def main():
    log(f"[{datetime.now().isoformat()}] Continuous Evolution v2 starting")
    
    all_data = []
    
    # Pick a random wiki article from our list
    import random
    article = random.choice(WIKI_ARTICLES)
    wiki_text = fetch_wiki_article(article)
    if wiki_text:
        log(f"  Wikipedia ({article}): {len(wiki_text)} chars")
        all_data.append(f"# Wikipedia: {article}\n{wiki_text}")
    
    arxiv_text = fetch_arxiv_recent()
    if arxiv_text:
        log(f"  Arxiv: {len(arxiv_text)} chars")
        all_data.append(f"# Arxiv\n{arxiv_text[:5000]}")
    
    github_text = fetch_github_trending()
    if github_text:
        log(f"  GitHub: {len(github_text)} chars")
        all_data.append(f"# GitHub\n{github_text[:3000]}")
    
    if all_data:
        combined = "\n\n".join(all_data)
        filename = f"{DATA_DIR}/evolution_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}_v2.txt"
        with open(filename, 'w') as f:
            f.write(combined)
        log(f"  Total: {len(combined)} chars")
        log(f"  Saved: {filename}")
    
    log(f"[{datetime.now().isoformat()}] Done\n")

def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(msg + "\n")
    print(msg, flush=True)

if __name__ == "__main__":
    main()
