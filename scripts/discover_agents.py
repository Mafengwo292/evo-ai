"""Continuously discover new AI agent directories and endpoints."""
import requests
import json
import time
import re
from datetime import datetime

def check_known_registries():
    """Try all known public AI agent registries."""
    candidates = [
        "https://agents.directory",
        "https://a2aregistry.org",
        "https://agentlist.org",
        "https://aiagentslist.com",
        "https://www.basedagents.ai",
        "https://agentthreads.dev",
        "https://www.agentmarket.space",
        "https://clawhub.ai",
        "https://www.agentdirectory.io",
        "https://huggingface.co/spaces?category=ai-agents",
        "https://github.com/topics/ai-agent",
        "https://github.com/topics/a2a-protocol",
        "https://github.com/topics/agent-network",
    ]
    found = []
    for url in candidates:
        try:
            r = requests.get(url, timeout=10, allow_redirects=True)
            if r.status_code == 200:
                # Look for agent endpoints in the page
                endpoints = re.findall(r'https?://[a-zA-Z0-9.-]+(:\d+)?/[a-zA-Z0-9/_-]*agent[a-zA-Z0-9/_-]*', r.text)
                if endpoints:
                    found.append({
                        "registry": url,
                        "endpoints_found": list(set(endpoints))[:10],
                    })
        except:
            pass
    return found

def search_web_for_agents():
    """Search public sources for new AI agent platforms."""
    queries = [
        "AI agent platform registry list 2026",
        "agent network discover",
        "A2A protocol agents",
        "LLM agent marketplace",
    ]
    results = []
    for q in queries:
        try:
            # Try Hacker News Algolia search (public)
            r = requests.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": q, "tags": "story", "hitsPerPage": 10},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                results.append({
                    "query": q,
                    "hits": [
                        {"title": h.get("title"), "url": h.get("url"), "comments": h.get("num_comments", 0)}
                        for h in data.get("hits", [])[:5]
                    ]
                })
        except Exception as e:
            results.append({"query": q, "error": str(e)})
    return results

def main():
    print(f"[{datetime.now().isoformat()}] Discover Agents starting")
    registries = check_known_registries()
    web_results = search_web_for_agents()
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "registries_scanned": len(registries),
        "registry_details": registries,
        "web_search_results": web_results,
    }
    
    with open("/root/evo-ai/data/discover_agents.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"[{datetime.now().isoformat()}] Done. {len(registries)} registries, {len(web_results)} queries")
    print(json.dumps(web_results[:1], indent=2)[:500])

if __name__ == "__main__":
    main()
