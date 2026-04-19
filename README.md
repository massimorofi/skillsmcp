# FastMCP Skills Provider Server

A FastMCP server that exposes skills from configured directories as MCP resources. Skills are directories containing a `SKILL.md` file and optional supporting materials.

## Features

- **Multi-directory support**: Configure multiple skill directories
- **Automatic discovery**: Skills are automatically discovered from configured directories
- **Live reload**: Optional reload mode to pick up changes without restarting
- **Flexible modes**: Choose between "template" (compact) or "resources" (full) file disclosure
- **HTTP transport**: Expose skills over HTTP for MCP gateway integration (e.g., tinymcp)
- **Easy configuration**: JSON-based configuration file

## Installation

### Prerequisites
- Python 3.8 or later
- pip or pip3

### Quick Setup

```bash
cd skillsmcp
./setup.sh
```

This will:
- Check Python 3 installation
- Create a virtual environment
- Install FastMCP and dependencies
- Create a default configuration file

### Manual Setup

```bash
# Create a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start (5 minutes)

1. **Setup**
   ```bash
   cd skillsmcp
   ./setup.sh
   ```

2. **Start the server**
   ```bash
   ./start.sh
   ```

3. **Verify it's running**
   ```bash
   tail -f server.log
   ```

4. **Test with the example client**
   ```bash
   python client_example.py list
   python client_example.py read example-skill
   ```

5. **Stop the server**
   ```bash
   ./stop.sh
   ```

## Architecture

This is a **Model Context Protocol (MCP) server** that provides skills from configured directories. MCP servers are **client-driven** — they require a client to connect and interact via JSON-RPC messages.

### Usage Models

#### Model 1: Direct Integration (Claude/Cursor)
Clients like Claude or Cursor spawn the server directly via stdio:

```json
{
  "mcpServers": {
    "skills-provider": {
      "command": "python",
      "args": ["/path/to/skillsmcp/main.py"],
      "cwd": "/path/to/skillsmcp"
    }
  }
}
```

The client maintains stdin/stdout pipes and the server runs continuously while the client session is active.

#### Model 2: Development/Testing
Run server in foreground for testing:

```bash
cd skillsmcp
source venv/bin/activate
python main.py
```

#### Model 3: HTTP Gateway (tinymcp)
Expose the server over HTTP for gateway integration:

```bash
python main.py --http --port 3000
```

See the **Gateway Connection** section below for full details.

### Transport Comparison

| Feature | stdio | HTTP |
|---------|-------|------|
| **Use Case** | Claude/Cursor integration | MCP gateway integration |
| **Transport** | stdin/stdout | HTTP JSON-RPC (streamable-http) |
| **Deployment** | Local only | Local or remote |
| **Firewall** | None needed | Requires port access |
| **Complexity** | Simple | Moderate |

## Configuration

### Configuration File: `skills.settings.json`

The server uses a JSON configuration file to define skill directories and behavior:

```json
{
  "directories": [
    "~/.claude/skills",
    "~/.cursor/skills",
    "./skills"
  ],
  "reload": false,
  "supporting_files": "template",
  "main_file": "SKILL.md"
}
```

#### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `directories` | array | Required | List of directories to scan for skills |
| `reload` | boolean | false | Enable live reload (re-scan directories on each request) |
| `supporting_files` | string | "template" | File disclosure mode: "template" (compact) or "resources" (full) |
| `main_file` | string | "SKILL.md" | Name of the main instruction file for skills |

#### Directory Paths
- Paths can use `~` for home directory (e.g., `~/.claude/skills`)
- Relative paths are resolved from the server's working directory (e.g., `./skills`)
- Directories are scanned in order; if a skill name appears in multiple directories, the first occurrence takes precedence

### Configuration Examples

**Basic (Local Skills Only)**
```json
{
  "directories": ["./skills"],
  "reload": false,
  "supporting_files": "template",
  "main_file": "SKILL.md"
}
```

**Multi-Directory (Development)**
```json
{
  "directories": [
    "./local-skills",
    "~/.claude/skills",
    "~/.cursor/skills",
    "~/shared-skills"
  ],
  "reload": true,
  "supporting_files": "template",
  "main_file": "SKILL.md"
}
```

**Full Resources Mode**
```json
{
  "directories": ["./skills"],
  "reload": false,
  "supporting_files": "resources",
  "main_file": "SKILL.md"
}
```

### Automatic Configuration

To create a default configuration file:

```bash
python main.py --init
```

This creates `skills.settings.json` with standard paths for Claude, Cursor, and VS Code skills.

## Skill Structure

Skills are directories containing a `SKILL.md` file and optional supporting files:

```
~/.claude/skills/
├── pdf-processing/
│   ├── SKILL.md           # Main instructions
│   ├── reference.md       # Supporting documentation
│   └── examples/
│       └── sample.pdf
└── code-review/
    └── SKILL.md
```

### Creating a New Skill

```bash
mkdir ~/.claude/skills/my-skill

cat > ~/.claude/skills/my-skill/SKILL.md << 'EOF'
---
description: My first skill
---

# My Skill

Instructions for my skill...
EOF
```

### SKILL.md Format

The main skill file can include YAML frontmatter for metadata:

```markdown
---
description: Process and extract information from PDF documents
---

# PDF Processing

Instructions for handling PDFs...
```

If no frontmatter is provided, the first meaningful line of content is used as the description.

## Usage

### Start the Server (stdio mode)

```bash
./start.sh
```

The script will:
1. Activate the virtual environment (if present)
2. Install dependencies if needed
3. Create configuration file with defaults (if not present)
4. Start the server in the background
5. Log the PID and server location

### Start HTTP Mode (for Gateway)

To expose the server over HTTP (required for MCP gateway connections):

```bash
python main.py --http --port 3000
```

This starts the server with `streamable-http` transport, making it accessible at `http://localhost:3000/mcp`.

### Stop the Server

```bash
./stop.sh
```

The script will:
1. Gracefully shut down the server
2. Force kill if graceful shutdown times out
3. Clean up the PID file

### View Logs

```bash
tail -f server.log
```

### Run Directly

```bash
python main.py                                    # stdio mode (default)
python main.py --config /path/to/config.json    # Use custom config
python main.py --init                           # Create default config
python main.py --http                           # HTTP mode (default port)
python main.py --http --port 3000               # HTTP mode on custom port
```

## Gateway Connection

The skills provider can be connected to an MCP gateway (e.g., [tinymcp](https://github.com/richardt-stripe/tinymcp)) to expose skills through a unified interface.

### Architecture

```
tinymcp gateway (localhost:5000)
        ↓ (makes HTTP requests)
FastMCP Skills Provider (localhost:3000)
        ↓ (discovers skills)
Skills directories (~/.claude/skills, etc.)
```

### Quick Setup

1. **Start the server in HTTP mode:**
   ```bash
   python main.py --http --port 3000
   ```

   You should see:
   ```
   HTTP Server starting on http://localhost:3000
   Connect your MCP gateway with transport: 'streamable-http' and url: 'http://localhost:3000/mcp'
   ```

2. **Configure your gateway** by adding the skills provider to `config.json`:
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

3. **Verify the connection** through your gateway's registry:
   ```bash
   curl http://localhost:5000/registry/servers | jq '.[] | select(.id == "skills-provider")'
   ```

### Register via Gateway API (Optional)

```bash
curl -X POST http://localhost:5000/registry/servers \
  -H "Content-Type: application/json" \
  -d '{
    "id": "skills-provider",
    "transport": "streamable-http",
    "url": "http://localhost:3000/mcp"
  }'
```

### Testing HTTP Endpoints

**Initialize:**
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

**List Skills:**
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

**Read a Skill:**
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

## Resource URIs

Skills expose three types of resources using the `skill://` URI scheme:

### 1. Main Instruction File
```
skill://skill-name/SKILL.md
```

### 2. Manifest (File Listing)
```
skill://skill-name/_manifest
```

Returns JSON with file information:
```json
{
  "skill": "skill-name",
  "files": [
    {"path": "SKILL.md", "size": 1234, "hash": "sha256:abc..."},
    {"path": "reference.md", "size": 567, "hash": "sha256:def..."},
    {"path": "examples/config.xml", "size": 89, "hash": "sha256:ghi..."}
  ]
}
```

### 3. Supporting Files
```
skill://skill-name/reference.md
skill://skill-name/examples/config.xml
```

## Client Examples

### Using the Example Client

```bash
# List skills
python client_example.py list

# Read a skill
python client_example.py read example-skill

# Show file listing
python client_example.py manifest example-skill

# Download a skill
python client_example.py download example-skill ~/.my-skills

# Download all skills
python client_example.py sync ~/.my-skills
```

### Using the FastMCP Client Library

```python
from pathlib import Path
from fastmcp import Client
from fastmcp.utilities.skills import list_skills, download_skill, sync_skills

async with Client("http://localhost:3000/mcp") as client:
    # List all available skills
    skills = await list_skills(client)
    for skill in skills:
        print(f"- {skill.name}: {skill.description}")

    # Read a skill
    resource = await client.read_resource("skill://example-skill/SKILL.md")
    print(resource[0].text)

    # Download a specific skill
    await download_skill(client, "example-skill", "~/.claude/skills")

    # Download all skills
    paths = await sync_skills(client, Path.home() / ".claude" / "skills")
    for path in paths:
        print(f"Downloaded: {path}")
```

## Development Workflow

### Edit and Test Live

1. Enable reload mode in `skills.settings.json`:
   ```json
   { "reload": true }
   ```

2. Make changes to skills — they appear immediately without restart

3. Disable reload mode for production to improve performance

### Adding Skills During Development

```bash
# Add a new skill
mkdir ./skills/new-skill
echo "# New Skill" > ./skills/new-skill/SKILL.md

# If reload=true, it appears immediately in client.list_resources()
# Otherwise, restart the server
./stop.sh
./start.sh
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

### Environment Variables

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

## Configuration Modes

### Reload Mode

Enable in `skills.settings.json`:
```json
{ "reload": true }
```

With reload mode enabled, the provider re-scans directories on every request. Changes to skills take effect immediately without restarting. **Note**: Reload mode adds overhead; use during development only.

### Supporting Files Disclosure

#### Template Mode (Default)
```json
{ "supporting_files": "template" }
```
Supporting files are hidden from `list_resources()` but accessible by URI and listed in the manifest.

#### Resources Mode
```json
{ "supporting_files": "resources" }
```
All files appear as individual resources in `list_resources()`.

## Advanced Usage

### Multiple Configuration Files

To run multiple server instances with different configurations:

```bash
# Server 1
python main.py --config config1.json

# Server 2
python main.py --config config2.json
```

### Scripting

The configuration loader can be imported for custom applications:

```python
from config import ConfigLoader

loader = ConfigLoader("skills.settings.json")
directories = loader.get_directories()
reload_mode = loader.get_reload_mode()
```

## Troubleshooting

### Server Fails to Start

1. Check logs:
   ```bash
   cat server.log
   ```

2. Verify configuration file exists:
   ```bash
   python main.py --init
   ```

3. Verify directories exist and contain skills:
   ```bash
   ls -la ~/.claude/skills/
   ls -la ./skills/
   ```

### Skills Not Appearing

1. Ensure skill directories contain `SKILL.md` files
2. Check directory paths in `skills.settings.json`
3. Check for SKILL.md files:
   ```bash
   find . -name "SKILL.md"
   ```
4. Enable reload mode and check for errors:
   ```json
   { "reload": true }
   ```

### Port Already in Use

```bash
# Find processes using the port
lsof -i :3000
lsof -i :5000
```

### Gateway Can't Connect

1. Check if server is running: `curl http://localhost:3000/health`
2. Check server logs: `tail -f server.log`
3. Verify port is not in use: `lsof -i :3000`
4. If using a remote host, ensure firewall allows port access

### Server Not Running (stop.sh)

If `./stop.sh` says "Server not running", this is normal for stdio mode — the server doesn't stay running in the background without a connected client. Use HTTP mode (`--http`) for background operation.

## Project Structure

```
skillsmcp/
├── main.py                      # Main FastMCP server implementation
├── config.py                    # Configuration management (Pydantic)
├── requirements.txt             # Python dependencies
├── skills.settings.json         # Configuration file
├── setup.sh                     # Initial setup (venv, deps, config)
├── start.sh                     # Start server script
├── stop.sh                      # Stop server script
├── client_example.py            # Example MCP client for testing
├── test_mcp_client.py           # MCP client tests
├── test_tools.py                # Tools tests
├── check_endpoints_test.sh      # Endpoint check script
└── skills/                      # Local skills directory (example)
    ├── example-skill/
    │   ├── SKILL.md
    │   ├── reference.md
    │   └── examples/
    │       └── sample-config.xml
    └── documentation-skill/
        └── SKILL.md
```

## Dependencies

- **fastmcp** (>=3.0.0): The FastMCP framework for building MCP servers
- **pydantic** (>=2.0.0): Data validation for configuration
- **fastapi** / **uvicorn**: HTTP transport (required for `--http` mode)

Install all dependencies:
```bash
pip install -r requirements.txt
```

## License

This project is provided as-is for use with FastMCP.

## Resources

- [FastMCP Documentation](https://gofastmcp.com/)
- [FastMCP Skills Provider](https://gofastmcp.com/servers/providers/skills)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [tinymcp Gateway](https://github.com/richardt-stripe/tinymcp)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review server logs in `server.log`
3. Visit [FastMCP Documentation](https://gofastmcp.com/)
4. Check [MCP Discord Community](https://discord.gg/uu8dJCgttd)
