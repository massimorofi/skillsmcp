# FastMCP Skills Provider - Quick Start Guide

## Overview

This is a fully functional FastMCP Skills Provider server that exposes skills from configured directories as MCP resources. The server automatically discovers skills containing a `SKILL.md` file and makes them available through the MCP protocol.

## Quick Start (5 minutes)

### 1. Initial Setup

```bash
cd skillsmcp
./setup.sh
```

This will:
- Check Python 3 installation
- Create a virtual environment
- Install FastMCP and dependencies
- Create a default configuration file

### 2. Start the Server

```bash
./start.sh
```

You should see:
```
✓ FastMCP Skills Provider Server started successfully (PID: ...)
  Log file: server.log
```

### 3. Verify It's Running

```bash
# Check logs
tail -f server.log

# In another terminal, stop the server
./stop.sh
```

## Project Structure

```
skillsmcp/
├── main.py                      # Main FastMCP server
├── config.py                    # Configuration loader
├── requirements.txt             # Python dependencies (FastMCP, pydantic)
├── skills.settings.json         # Configuration file
├── setup.sh                     # Setup script (creates venv, installs deps)
├── start.sh                     # Start server script
├── stop.sh                      # Stop server script
├── README.md                    # Full documentation
├── QUICKSTART.md                # This file
├── .gitignore                   # Git ignore rules
└── skills/
    ├── example-skill/           # Example skill
    │   ├── SKILL.md            # Main instruction file
    │   ├── reference.md        # Supporting documentation
    │   └── examples/
    │       └── sample-config.xml
    └── documentation-skill/     # Another example skill
        └── SKILL.md
```

## Key Files Explained

### main.py
The FastMCP server implementation that:
- Loads configuration from `skills.settings.json`
- Creates a `SkillsDirectoryProvider` with configured directories
- Exposes skills as MCP resources via the `skill://` URI scheme

### config.py
Configuration management that:
- Validates JSON configuration using Pydantic models
- Handles directory path expansion (`~` for home directory)
- Provides methods to reload configuration

### skills.settings.json
JSON configuration with:
- `directories`: List of skill directories to scan (supports `~` paths and relative paths)
- `reload`: Enable live reload (changes take effect without restart)
- `supporting_files`: "template" (default) or "resources" for file disclosure mode
- `main_file`: Name of main instruction file (default: "SKILL.md")

## Configuration Examples

### Basic Configuration (Local Skills Only)
```json
{
  "directories": ["./skills"],
  "reload": false,
  "supporting_files": "template",
  "main_file": "SKILL.md"
}
```

### Multi-Directory with Development Mode
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

### Full Resources Disclosure Mode
```json
{
  "directories": ["./skills"],
  "reload": false,
  "supporting_files": "resources",
  "main_file": "SKILL.md"
}
```

## Creating a New Skill

Create a directory with a `SKILL.md` file:

```bash
# Create skill directory
mkdir ~/.claude/skills/my-skill

# Create main instruction file
cat > ~/.claude/skills/my-skill/SKILL.md << 'EOF'
---
description: My first skill
---

# My Skill

Instructions for my skill...
EOF

# Optionally add supporting files
echo "Additional docs..." > ~/.claude/skills/my-skill/reference.md
```

The skill will be discovered automatically if reload mode is enabled, or on server restart.

## Using with MCP Clients

### List Available Skills
```python
from fastmcp import Client
from fastmcp.utilities.skills import list_skills

async with Client("http://localhost:5000/mcp") as client:
    skills = await list_skills(client)
    for skill in skills:
        print(f"- {skill.name}: {skill.description}")
```

### Read a Skill
```python
from fastmcp import Client

async with Client("http://localhost:5000/mcp") as client:
    # Read the main instruction file
    resource = await client.read_resource("skill://example-skill/SKILL.md")
    print(resource[0].text)
    
    # Read the manifest (file listing)
    manifest = await client.read_resource("skill://example-skill/_manifest")
    print(manifest[0].text)
```

### Download a Skill
```python
from pathlib import Path
from fastmcp import Client
from fastmcp.utilities.skills import download_skill

async with Client("http://localhost:5000/mcp") as client:
    # Download skill to ~/.claude/skills
    path = await download_skill(
        client, 
        "example-skill",
        Path.home() / ".claude" / "skills"
    )
    print(f"Downloaded to: {path}")
```

### List and Download All Skills
```python
from pathlib import Path
from fastmcp import Client
from fastmcp.utilities.skills import sync_skills

async with Client("http://localhost:5000/mcp") as client:
    # Download all skills
    paths = await sync_skills(client, Path.home() / ".claude" / "skills")
    for path in paths:
        print(f"Downloaded: {path}")
```

## Resource URI Format

Skills expose three types of resources:

### 1. Main Instruction File
```
skill://skill-name/SKILL.md
```

### 2. Manifest (File Listing)
```
skill://skill-name/_manifest
```

Returns:
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

## Development Workflow

### Edit and Test Live
1. Enable reload mode in `skills.settings.json`:
   ```json
   {
     "reload": true
   }
   ```

2. Make changes to skills - they appear immediately without restart

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

## Troubleshooting

### Skills Not Appearing
1. Check configuration:
   ```bash
   cat skills.settings.json
   ```

2. Verify directories exist:
   ```bash
   ls -la ~/.claude/skills/
   ls -la ./skills/
   ```

3. Check for SKILL.md files:
   ```bash
   find . -name "SKILL.md"
   ```

4. Review server logs:
   ```bash
   cat server.log
   ```

### Server Won't Start
1. Check Python installation:
   ```bash
   python3 --version
   ```

2. Run setup again:
   ```bash
   ./setup.sh
   ```

3. Check logs:
   ```bash
   cat server.log
   ```

### Port in Use
If the default FastMCP port is in use, check what's running:
```bash
lsof -i :5000  # Adjust port number as needed
```

## Commands Reference

| Command | Purpose |
|---------|---------|
| `./setup.sh` | Initial setup (venv, dependencies, configuration) |
| `./start.sh` | Start server in background |
| `./stop.sh` | Stop running server |
| `python main.py --init` | Create default configuration |
| `python main.py --config /path/to/config.json` | Run with custom config |
| `tail -f server.log` | View live server logs |
| `cat server.log` | View all server logs |

## Next Steps

1. **Customize Configuration**: Edit `skills.settings.json` with your skill directories
2. **Add Skills**: Place skill directories in configured locations
3. **Deploy**: Use start/stop scripts for your deployment
4. **Integrate**: Use FastMCP client utilities to access skills

## Resources

- [FastMCP Documentation](https://gofastmcp.com/)
- [FastMCP Skills Provider](https://gofastmcp.com/servers/providers/skills)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [FastMCP Discord](https://discord.gg/uu8dJCgttd)

## License

This project is provided as an example MCP server implementation.
