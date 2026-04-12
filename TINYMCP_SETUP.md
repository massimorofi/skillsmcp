# Quick Setup: Connect FastMCP Skills Provider to tinymcp Gateway

## Step 1: Start the Skills Provider in HTTP Mode

```bash
cd /home/briggen/Dev/code/python/skillsmcp
source venv/bin/activate
python main.py --http --port 3000
```

You'll see:
```
HTTP Server starting on http://localhost:3000
Connect your MCP gateway with transport: 'streamable-http' and url: 'http://localhost:3000/mcp'
```

## Step 2: Configure tinymcp Gateway

In your tinymcp `config.json`, add:

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

**Location:** `/home/briggen/Dev/code/python/tinymcp/config.json`

## Step 3: Verify Connection

In the tinymcp gateway:

```bash
curl http://localhost:5000/registry/servers | jq '.[] | select(.id == "skills-provider")'
```

Should show your skills provider listed.

## That's It!

Your FastMCP Skills Provider is now connected to the tinymcp gateway. Skills are instantly available through the gateway's unified interface!

## Troubleshooting

**Gateway can't connect?**
```bash
# Check if server is running
curl http://localhost:3000/health

# Check server logs
cd /home/briggen/Dev/code/python/skillsmcp
tail -f server.log
```

**Need different port?**
```bash
# Start on custom port
python main.py --http --port 8000

# Update config.json
"url": "http://localhost:8000/mcp"
```

## Advanced: Run Both Simultaneously

Terminal 1 - HTTP Server (for gateway):
```bash
cd /home/briggen/Dev/code/python/skillsmcp
python main.py --http --port 3000
```

Terminal 2 - tinymcp Gateway:
```bash
cd /home/briggen/Dev/code/python/tinymcp
./scripts/start.sh
```

Then your skills are available through the gateway dashboard!

For detailed documentation, see [HTTP_GATEWAY_GUIDE.md](HTTP_GATEWAY_GUIDE.md)
