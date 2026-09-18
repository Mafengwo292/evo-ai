#!/bin/bash
# Discover real AI agent registry APIs

REGISTRIES=(
    "https://agentlookup.dev"
    "https://basedagents.ai"
    "https://aiia.ro"
    "https://waggle.zone"
    "https://aistatus.cc"
    "https://api.agentthreads.dev"
    "https://agents.ai"
    "https://www.agent.ai"
    "https://www.aiagentsdirectory.com"
    "https://aiagentslist.com"
    "https://directoryofagents.com"
    "https://agents.live"
    "https://clawdhub.com"
    "https://openagent.bot"
    "https://agentlist.io"
    "https://agentndx.com"
    "https://llmexplorer.com"
    "https://agentlux.com"
    "https://openwork.com"
    "https://hol.org"
    "https://truefoundry.com"
)

PATHS=(
    "/api"
    "/api/agents"
    "/api/v1/agents"
    "/api/registry"
    "/api/v1/registry"
    "/registry"
    "/api/register"
    "/register"
    "/openapi.json"
    "/docs"
    "/api/docs"
)

echo "Scanning ${#REGISTRIES[@]} registries × ${#PATHS[@]} paths"
for reg in "${REGISTRIES[@]}"; do
    for path in "${PATHS[@]}"; do
        url="$reg$path"
        code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)
        if [[ "$code" == "200" || "$code" == "201" || "$code" == "405" ]]; then
            echo "  [$code] $url"
        fi
    done
done