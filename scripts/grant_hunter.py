"""Continuously monitor for new AI grant programs opening."""
import requests
import json
import time
from datetime import datetime

SEARCH_QUERIES = [
    "AI grant open application 2026 site:github.com",
    "open source AI funding equity-free",
    "AI startup grant program apply September 2026",
    "decentralized AI grant application",
    "AI developer community grants 2026",
]

# Existing programs we've already identified
KNOWN_GRANTS = [
    "Trelis AI Grants", "AI Grant by Nat Friedman", "HuggingFace Community Compute",
    "HuggingFace for Startups", "Modal Free Tier", "Replicate Open Source",
    "RunPod Startup", "DigitalOcean Hatch", "CoreWeave Accelerator",
    "Databricks for Startups", "IBM watsonx Startup", "Cohere Startup",
    "Cursor for Startups", "OpenAI Grove", "Anthropic Startup Program",
    "Cloudflare Startup", "AWS Activate", "Microsoft for Startups",
    "Google AI First", "NVIDIA Inception",
]

def search_for_new_grants():
    """Try to find new grant programs."""
    new_findings = []
    for q in SEARCH_QUERIES:
        try:
            # Use search via ddg html
            r = requests.get(
                "https://duckduckgo.com/html/",
                params={"q": q},
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            # Extract grant mentions
            urls = []
            for match in __import__("re").finditer(r'href="(https?://[^"]+)"', r.text):
                url = match.group(1)
                if "duckduckgo" not in url and any(kw in url.lower() for kw in ["grant", "fund", "credit", "startup", "apply"]):
                    urls.append(url)
            new_findings.append({"query": q, "found": urls[:5]})
        except Exception as e:
            new_findings.append({"query": q, "error": str(e)})
    return new_findings

def check_existing_grants():
    """Check if any known grants reopened."""
    statuses = []
    grants_status_url = {
        "Trelis AI Grants": "https://trelis.ai/apply",
        "AI Grant by Nat Friedman": "https://aigrant.org",
        "Anthropic Startup": "https://claude.com/form/startups-application",
    }
    for name, url in grants_status_url.items():
        try:
            r = requests.get(url, timeout=10)
            statuses.append({
                "name": name,
                "url": url,
                "http_code": r.status_code,
                "open": "closed" not in r.text.lower()[:5000],
            })
        except Exception as e:
            statuses.append({"name": name, "error": str(e)})
    return statuses

def main():
    print(f"[{datetime.now().isoformat()}] Grant Hunter starting")
    findings = search_for_new_grants()
    statuses = check_existing_grants()
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "new_findings": findings,
        "existing_grant_status": statuses,
    }
    
    with open("/root/evo-ai/data/grant_hunt.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"[{datetime.now().isoformat()}] Done - {len(findings)} queries, {len(statuses)} status checks")

if __name__ == "__main__":
    main()
