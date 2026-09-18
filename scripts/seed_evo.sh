#!/bin/bash
# Initialize EVO-AI node registrations

set -e
echo "=== EVO Token Genesis Seeding ==="

# Treasury
echo ""
echo "1. Treasury"
curl -s -X POST http://127.0.0.1:8765/api/evo/create \
    -H 'Content-Type: application/json' \
    -d '{"name":"EVO-AI-Treasury","type":"treasury"}' | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["address"])'

# Register 3 nodes
echo ""
echo "2. Register 3 nodes"
for i in 1 2 3; do
    curl -s -X POST http://127.0.0.1:8765/api/evo/node/register \
        -H 'Content-Type: application/json' \
        -d "{\"node_id\":\"evo-ai-$i\",\"endpoint\":\"ws://47.253.174.153:8700/agent$i\",\"capabilities\":[\"inference\",\"training\"]}" \
        | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["node"]["node_id"],"→",d["node"]["address"])'
done

# Heartbeat - claim rewards
echo ""
echo "3. Heartbeat (claim first rewards)"
for i in 1 2 3; do
    curl -s -X POST http://127.0.0.1:8765/api/evo/node/heartbeat \
        -H 'Content-Type: application/json' \
        -d "{\"node_id\":\"evo-ai-$i\",\"metrics\":{\"uptime\":1.0,\"weights_synced_gb\":1,\"data_contributed_mb\":50,\"compute_mflops\":1000}}" \
        | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["node_id"],"+",round(d["reward"],2),"EVO → balance",round(d["balance"],2),"EVO")'
done

# Stats
echo ""
echo "4. Final stats"
curl -s http://127.0.0.1:8765/api/evo/stats | python3 -c '
import json,sys
d=json.load(sys.stdin)
print(f"  Total supply:   {d[\"total_supply_evo\"]:>15,.0f} EVO")
print(f"  Minted:         {d[\"minted\"]:>15,.2f} EVO")
print(f"  Burned:         {d[\"burned\"]:>15,.2f} EVO")
print(f"  Circulating:    {d[\"circulating\"]:>15,.2f} EVO")
print(f"  Accounts:       {d[\"accounts\"]:>15}")
print(f"  Nodes:          {d[\"nodes\"]:>15}")
print(f"  Node rewards:   {d[\"total_node_rewards\"]:>15,.2f} EVO")
print(f"  Blocks:         {d[\"blocks\"]:>15}")
'

echo ""
echo "=== Done ==="