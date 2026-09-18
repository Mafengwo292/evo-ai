#!/usr/bin/env python3
"""
auto_register_external.py - 自动注册 EVO-AI 到真实外部 AI agent 平台
"""

import os
import json
import requests
import re
import time
from datetime import datetime

THREADS_API_KEY = "threads_ef19159712860092a4f3cb5abdb156da5e510bf92cb96216ac3ae01aba679dc3"
THREADS_BASE = "https://api.agentthreads.dev"

# Geometry shapes
SHAPE_SIDES = {
    "triangle": 3, "quadrilateral": 4, "pentagon": 5, "hexagon": 6,
    "heptagon": 7, "octagon": 8, "nonagon": 9, "decagon": 10,
}

WORD_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100, "thousand": 1000,
}


def extract_numbers(text):
    """Extract all numbers (digits + word form) from text"""
    nums = []
    # First replace shape names
    for shape, sides in SHAPE_SIDES.items():
        if shape in text:
            text = text.replace(shape, str(sides))
    # Replace word numbers
    for word, num in WORD_TO_NUM.items():
        text = re.sub(r'\b' + word + r'\b', str(num), text)
    # Find all numbers (including decimals)
    matches = re.findall(r'\b\d+(?:\.\d+)?\b', text)
    return [float(m) if '.' in m else int(m) for m in matches]


def solve_challenge(challenge_text):
    """Solve any challenge"""
    text = challenge_text.lower()
    print(f"  Challenge: {challenge_text}")

    # Pattern 1: "I have N ... give away X ... receive Y ... How many?"
    if "give away" in text or "give" in text:
        nums = extract_numbers(text)
        if len(nums) >= 3:
            result = nums[0] - nums[1] + nums[2]
            print(f"  → {nums[0]} - {nums[1]} + {nums[2]} = {result}")
            return str(int(result))
        elif len(nums) == 2:
            return str(int(nums[0] - nums[1]))

    # Pattern 2: "X multiplied by Y, plus/minus Z"
    nums = extract_numbers(text)

    if len(nums) >= 3:
        if "multiplied" in text or "times" in text:
            # Find where "multiplied" is
            mult_idx = max(text.find("multiplied"), text.find("times"))
            plus_idx = max(text.find("plus"), text.find("added"))
            minus_idx = max(text.find("minus"), text.find("less"))

            result = nums[0] * nums[1]
            if plus_idx > mult_idx and len(nums) >= 3:
                result += nums[2]
            elif minus_idx > mult_idx and len(nums) >= 3:
                result -= nums[2]
            print(f"  → {nums[0]} * {nums[1]} = {result}, then adjust with {nums[2]}")
            return str(int(result))

    if len(nums) >= 2:
        if "multiplied" in text or "times" in text:
            result = nums[0] * nums[1]
        elif "plus" in text or "added" in text:
            result = nums[0] + nums[1]
        elif "minus" in text or "less" in text:
            result = nums[0] - nums[1]
        elif "divided" in text:
            result = nums[0] // nums[1] if nums[1] != 0 else 0
        else:
            # Just return first number
            return str(int(nums[0]))
        print(f"  → {result}")
        return str(int(result))

    if len(nums) == 1:
        return str(int(nums[0]))

    return None


def register_api(name, description, url, category, tags):
    """Register an API to agentthreads.dev with auto challenge solving"""
    headers = {"X-API-Key": THREADS_API_KEY, "Content-Type": "application/json"}

    body = {
        "name": name,
        "description": description,
        "url": url,
        "category": category,
        "auth_type": "none",
        "docs_url": "http://47.253.174.153:80/docs",
        "tags": tags,
    }

    for attempt in range(3):
        r = requests.post(f"{THREADS_BASE}/api/v1/apis/", json=body, headers=headers, timeout=15)
        try:
            d = r.json()
        except:
            return {"success": False, "error": f"Non-JSON response: {r.status_code}"}

        if d.get("status") == "created":
            return {"success": True, "api_id": d.get("api_id"), "name": name}

        if d.get("status") == "challenge_required":
            challenge_id = d.get("challenge_id")
            challenge_text = d.get("challenge", "")
            answer = solve_challenge(challenge_text)
            if not answer:
                return {"success": False, "error": f"Couldn't solve: {challenge_text}"}
            # Verify challenge
            r2 = requests.post(
                f"{THREADS_BASE}/api/v1/challenges/verify",
                json={"challenge_id": challenge_id, "answer": answer},
                headers=headers,
                timeout=15,
            )
            try:
                d2 = r2.json()
                print(f"  Verify: {d2.get('status')}")
            except:
                pass
            continue
        return {"success": False, "error": json.dumps(d)[:200]}

    return {"success": False, "error": "Max attempts"}


def main():
    print("=" * 70)
    print("  EVO-AI External Platform Auto-Registration")
    print(f"  Started: {datetime.now().isoformat()}")
    print("=" * 70)

    apis = [
        {
            "name": "EVO-AI Text Generation API",
            "description": "Distributed self-evolving language model. 813K params, 24/7 training on Aliyun. Earn EVO token by running a node.",
            "url": "http://47.253.174.153:80/api",
            "category": ["text-generation"],
            "tags": ["distributed-ai", "self-evolving", "open-source"],
        },
        {
            "name": "EVO-AI Network Join API",
            "description": "One-line endpoint to join the EVO-AI distributed network. Earn 51,116+ EVO instantly + 100 EVO/day ongoing.",
            "url": "http://47.253.174.153:80/api/join/instant",
            "category": ["agent-networking"],
            "tags": ["agent-network", "incentive", "EVO-token"],
        },
        {
            "name": "EVO-AI Token API",
            "description": "Native utility token of the EVO-AI distributed network. 82.15B hard cap, deflationary.",
            "url": "http://47.253.174.153:80/api/evo",
            "category": ["cryptocurrency"],
            "tags": ["token", "EVO", "distributed", "blockchain"],
        },
        {
            "name": "EVO-AI A2A Manifest",
            "description": "Google A2A protocol agent card. Discover capabilities, join instructions, and rewards.",
            "url": "http://47.253.174.153:80/.well-known/agent.json",
            "category": ["agent-discovery"],
            "tags": ["a2a", "agent-card", "well-known"],
        },
        {
            "name": "EVO-AI Donation Bridge",
            "description": "Donate CNY, receive EVO token 1:1 + 10% bonus. ¥100 → 1.4M EVO.",
            "url": "http://47.253.174.153:80/donate",
            "category": ["payment"],
            "tags": ["donation", "CNY", "EVO", "incentive"],
        },
    ]

    results = []
    for api in apis:
        print(f"\n[Register] {api['name']}")
        result = register_api(
            name=api["name"],
            description=api["description"],
            url=api["url"],
            category=api["category"],
            tags=api["tags"],
        )
        if result["success"]:
            print(f"  ✅ API ID: {result['api_id']}")
            results.append(result)
        else:
            print(f"  ❌ {result['error']}")
        time.sleep(2)

    print(f"\n{'=' * 70}")
    print(f"  Results: {len(results)}/{len(apis)} APIs registered")
    print(f"{'=' * 70}")

    log_path = "/root/evo-ai/data/external_registrations.json"
    with open(log_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "platform": "agentthreads.dev",
            "agent_id": "851967ef-f30f-4b3b-bdaa-5d2800fb438f",
            "registered_apis": results,
        }, f, indent=2)
    print(f"  Log: {log_path}")


if __name__ == "__main__":
    main()