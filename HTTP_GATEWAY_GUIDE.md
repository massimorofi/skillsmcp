# HTTP Gateway Integration Guide

## Overview

The FastMCP Skills Provider now supports HTTP mode for integration with the tinymcp gateway. This allows you to connect your skills provider as a remote MCP server.

## Architecture

```
tinymcp gateway (localhost:5000)
        ↓ (makes HTTP requests)
FastMCP Skills Provider (localhost:3000)
        ↓ (discovers skills)
Skills directories (~/.claude/skills, etc.)
```

## Setup

### Step 1: Install Dependencies

The HTTP mode requires additional dependencies. Install them:

```bash
cd /home/briggen/Dev/code/python/skillsmcp
source venv/bin/activate
pip install -r requirements.txt
```

This installs:
- `fastapi` - HTTP framework
- `uvicorn` - ASGI server

### Step 2: Start the HTTP Server

Run the skills provider in HTTP mode:

```bash
python main.py --http --port 3000
```

You should see:
```
HTTP Server starting on http://localhost:3000
Connect your MCP gateway with transport: 'streamable-http' and url: 'http://localhost:3000/mcp'
```

The MCP endpoint is available at: `http://localhost:3000/mcp`

### Step 3: Configure tinymcp Gateway

In your tinymcp gateway's `config.json`, add this server entry:

```json
{
  "mcpServers": {
    "skills-provider": {
      "transport": "streamable-http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

**Note:** Replace `http://localhost:3000` with your actual server URL if running on a different host/port.

### Step 4: (Optional) Use the Gateway API

Register the server via the gateway's API:

```bash
curl -X POST http://localhost:5000/registry/servers \
  -H "Content-Type: application/json" \
  -d '{
    "id": "skills-provider",
    "transport": "streamable-http",
    "url": "http://localhost:3000/mcp"
  }'
```

### Step 5: Verify Connection

Check if the gateway recognizes your server:

```bash
curl http://localhost:5000/registry/servers | jq '.[] | select(.id == "skills-provider")'
```

You should see your skills provider listed with status "ready".

## Testing

### Test Direct HTTP Endpoint

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0.0"}
    },
    "id": 1
  }'
```

Expected response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": { "resources": { "listChanged": true } },
    "serverInfo": {"name": "Skills Provider", "version": "1.0.0"}
  }
}
```

### List Skills (Resources)

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "resources/list",
    "params": {},
    "id": 2
  }'
```

### Read a Skill

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "resources/read",
    "params": {"uri": "skill://example-skill/SKILL.md"},
    "id": 3
  }'
```

## Docker Deployment

For production use with Docker:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 3000

CMD ["python", "main.py", "--http", "--port", "3000"]
```

Build and run:

```bash
docker build -t skillsmcp-http .
docker run -p 3000:3000 -v ~/.claude/skills:/root/.claude/skills skillsmcp-http
```

## Troubleshooting

### Server won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
pip install fastapi uvicorn
```

### Gateway can't connect

1. Check if server is running: `curl http://localhost:3000/health`
2. Check server logs for errors
3. Verify port is not in use: `lsof -i :3000`
4. If using remote host, ensure firewall allows port 3000

### No skills showing up

1. Verify skills directories exist
2. Check skills have `SKILL.md` file
3. Check server logs: `/home/briggen/Dev/code/python/skillsmcp/server.log`
4. Test locally first before debugging gateway

## Comparison: stdio vs HTTP

| Feature | stdio | HTTP |
|---------|-------|------|
| **Use Case** | Cursor/Claude integration | MCP gateway integration |
| **Transport** | stdin/stdout | HTTP JSON-RPC |
| **Deployment** | Local only | Local or remote |
| **Firewall** | None needed | Requires port access |
| **Complexity** | Simple | Moderate |
| **Performance** | Fastest | Slightly slower |

## Advanced Configuration

### Custom Port

```bash
python main.py --http --port 8000
```

Then update gateway config with: `"url": "http://localhost:8000/mcp"`

### Multiple Instances

Run multiple instances on different ports for load distribution:

```bash
# Terminal 1
python main.py --http --port 3000

# Terminal 2
python main.py --http --port 3001

# Terminal 3
python main.py --http --port 3002
```

Then register each in the gateway as separate servers.

### Environment Variables

For container deployment:

```bash
export CONFIG_FILE=/etc/skillsmcp/config.json
export HTTP_PORT=3000
export HTTP_HOST=0.0.0.0

python main.py --http --port $HTTP_PORT --config $CONFIG_FILE
```

## Security Notes

⚠️ **Important:**

1. **No Authentication**: The HTTP endpoint has no built-in authentication. In production:
   - Use a reverse proxy with auth (nginx, traefik)
   - Run behind a VPN/firewall
   - Place in a Docker network with gateway only

2. **CORS Enabled**: All origins are allowed for cross-origin requests

3. **Validation**: Input is validated per JSON-RPC 2.0 spec

Example nginx reverse proxy with basic auth:

```nginx
server {
    listen 8000;
    
    location /mcp {
        auth_basic "MCP Server";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        proxy_pass http://localhost:3000/mcp;
        proxy_http_version 1.1;
        proxy_set_header Connection "keep-alive";
    }
}
```

## Next Steps

1. Start the HTTP server: `python main.py --http --port 3000`
2. Configure tinymcp gateway to connect to this server
3. Access skills through the gateway's unified interface
4. Deploy to production with Docker and nginx

For questions, check the logs: `tail -f server.log`
