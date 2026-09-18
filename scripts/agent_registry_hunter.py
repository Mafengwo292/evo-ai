"""Continuously discover and register EVO-AI on new public AI agent registries."""
import requests
import json
import time
from datetime import datetime

KNOWN_REGISTRIES = [
    {"name": "BasedAgents.ai", "register_url": "https://basedagents.ai/api/agents", "agent_id_field": "id"},
    {"name": "AgentThreads.dev", "register_url": "https://agentthreads.dev/api/agents", "agent_id_field": "id"},
    {"name": "A2ARegistry.org", "register_url": "https://a2aregistry.org/api/agents", "agent_id_field": "id"},
    {"name": "AgentDirectory.io", "register_url": "https://agentdirectory.io/api/register", "agent_id_field": "id"},
    {"name": "AgentMarket.space", "register_url": "https://agentmarket.space/api/agents", "agent_id_field": "id"},
    {"name": "ClawHub.ai", "register_url": "https://clawhub.ai/api/skills", "agent_id_field": "id"},
]

# Public registries to discover
DISCOVERY_QUERIES = [
    "AI agent marketplace register",
    "LLM agent directory submit",
    "AI assistant registry list",
    "agent network registry 2026",
]

AGENT_CARD = {
    "name": "EVO-AI",
    "description": "Distributed self-evolving language model network. 813K params, evolutionary model merging, A2A JSON-RPC 2.0 endpoint.",
    "url": "http://47.253.174.153:80",
    "version": "1.0.0",
    "capabilities": ["text-generation", "evolution", "distributed-inference", "a2a-protocol"],
    "skills": ["chat", "evolution-summary", "token-balance", "node-discovery"],
}

def attempt_register(reg):
    """Try to register EVO-AI on a known registry."""
    try:
        r = requests.post(reg["register_url"], json=AGENT_CARD, timeout=15)
        return {
            "registry": reg["name"],
            "status_code": r.status_code,
            "success": 200 <= r.status_code < 300,
            "response": r.text[:300],
        }
    except Exception as e:
        return {"registry": reg["name"], "success": False, "error": str(e)[:200]}

def discover_via_search():
    """Search for new registries."""
    results = []
    for q in DISCOVERY_QUERIES:
        try:
            # Use a public search API
            r = requests.get(f"https://duckduckgo.com/html/?q={requests.utils.quote(q)}", timeout=10)
            # Extract URLs from search results
            urls = []
            for match in re.finditer(r'href="(https?://[^"]+)"', r.text):
                url = match.group(1)
                if "duckduckgo" not in url and "ad_domain" not in url:
                    urls.append(url)
            results.append({"query": q, "urls_found": urls[:10]})
        except Exception as e:
            results.append({"query": q, "error": str(e)})
    return results

import re

def main():
    print(f"[{datetime.now().isoformat()}] Agent Registry Hunter starting")
    
    # 1. Try registration on known registries
    reg_results = []
    for reg in KNOWN_REGISTRIES:
        result = attempt_register(reg)
        print(f"  {reg['name']}: {result.get('status_code', 'ERR')}")
        reg_results.append(result)
    
    # 2. Discover new ones
    discoveries = discover_via_search()
    
    # 3. Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "known_registry_attempts": reg_results,
        "discoveries": discoveries[:5],  # truncate
    }
    
    with open("/root/evo-ai/data/registry_hunt.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"[{datetime.now().isoformat()}] Done")

if __name__ == "__main__":
    main()
