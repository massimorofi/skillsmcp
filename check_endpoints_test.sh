#!/bin/bash
set -e

echo "=== Testing Skills Provider Tools via tinymcp Gateway ==="
echo ""

# First, ensure skills-provider is registered in tinymcp config
echo "Checking if skills-provider is registered..."
if ! grep -q "skills-provider" /home/briggen/Dev/code/python/tinymcp/config.json 2>/dev/null; then
  echo "Registering skills-provider server..."
  curl -s -X POST http://localhost:8000/registry/servers \
    -H "Content-Type: application/json" \
    -d '{
      "id": "skills-provider",
      "transport": "streamable-http",
      "url": "http://localhost:3001/mcp"
    }' | jq .
  echo ""
fi

echo "1. Listing tools from skills-provider..."
curl -s -X GET "http://localhost:8000/tools?server=skills-provider" | jq .

echo ""
echo "2. Testing list_skills tool..."
SESSION=$(curl -s -X POST http://localhost:8000/sessions | jq -r '.sessionId')
curl -s -X POST "http://localhost:8000/execute?server=skills-provider" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "list_skills", "arguments": {}},
    "id": 1
  }' | jq .

echo ""
echo "3. Testing get_skill tool..."
curl -s -X POST "http://localhost:8000/execute?server=skills-provider" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "get_skill", "arguments": {"skill_name": "example-skill"}},
    "id": 2
  }' | jq .

echo ""
echo "4. Testing list_skill_files tool..."
curl -s -X POST "http://localhost:8000/execute?server=skills-provider" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "list_skill_files", "arguments": {"skill_name": "example-skill"}},
    "id": 3
  }' | jq .

echo ""
python test_mcp_client.py
