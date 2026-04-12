# FastMCP Skills Provider Server

A FastMCP server that exposes skills from configured directories as MCP resources. Skills are directories containing a `SKILL.md` file and optional supporting materials.

## Features

- **Multi-directory support**: Configure multiple skill directories
- **Automatic discovery**: Skills are automatically discovered from configured directories
- **Live reload**: Optional reload mode to pick up changes without restarting
- **Flexible modes**: Choose between "template" (compact) or "resources" (full) file disclosure
- **Easy configuration**: JSON-based configuration file

## Installation

### Prerequisites
- Python 3.8 or later
- pip or pip3

### Setup

```bash
# Clone or navigate to the project directory
cd skillsmcp

# Create a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

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

### Start the Server

To start the server:

```bash
./start.sh
```

The script will:
1. Activate the virtual environment (if present)
2. Install dependencies if needed
3. Create configuration file with defaults (if not present)
4. Start the server in the background
5. Log the PID and server location

### Stop the Server

To stop the server:

```bash
./stop.sh
```

The script will:
1. Gracefully shut down the server
2. Force kill if graceful shutdown times out
3. Clean up the PID file

### View Logs

The server logs to `server.log`:

```bash
# View recent logs
tail -f server.log

# View all logs
cat server.log
```

### Run Directly

You can also run the server directly with Python:

```bash
python main.py                                    # Use skills.settings.json
python main.py --config /path/to/config.json    # Use custom config
python main.py --init                           # Create default config
```

## Resource URIs

Skills expose resources using the `skill://` URI scheme:

### Main Instruction File
```
skill://pdf-processing/SKILL.md
```

### Manifest (file listing)
```
skill://pdf-processing/_manifest
```

Returns JSON with file information:
```json
{
  "skill": "pdf-processing",
  "files": [
    {"path": "SKILL.md", "size": 1234, "hash": "sha256:abc123..."},
    {"path": "reference.md", "size": 567, "hash": "sha256:def456..."}
  ]
}
```

### Supporting Files
```
skill://pdf-processing/reference.md
skill://pdf-processing/examples/sample.pdf
```

## Example: Using with a Client

```python
from fastmcp import Client
from fastmcp.utilities.skills import list_skills, download_skill

async with Client("http://localhost:5000/mcp") as client:
    # List all available skills
    skills = await list_skills(client)
    for skill in skills:
        print(f"{skill.name}: {skill.description}")
    
    # Download a specific skill
    await download_skill(client, "pdf-processing", "~/.claude/skills")
```

## Configuration Modes

### Reload Mode

Enable in `skills.settings.json`:
```json
{
  "reload": true
}
```

With reload mode enabled, the provider re-scans directories on every request. Changes to skills take effect immediately without restarting. **Note**: Reload mode adds overhead; use during development only.

### Supporting Files Disclosure

#### Template Mode (Default)
```json
{
  "supporting_files": "template"
}
```
Supporting files are hidden from `list_resources()` but accessible by URI and listed in the manifest.

#### Resources Mode
```json
{
  "supporting_files": "resources"
}
```
All files appear as individual resources in `list_resources()`.

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
   ls -la ~/.cursor/skills/
   ```

### Skills Not Appearing

1. Ensure skill directories contain `SKILL.md` files
2. Check directory paths in `skills.settings.json`
3. Enable reload mode and check for errors:
   ```json
   {
     "reload": true
   }
   ```

### Port Already in Use

If the default port is in use, modify your FastMCP configuration or check for existing processes:

```bash
# Find processes using the port (adjust port number as needed)
lsof -i :5000
```

## Project Structure

```
skillsmcp/
├── main.py                 # Main server implementation
├── config.py              # Configuration loader
├── requirements.txt       # Python dependencies
├── skills.settings.json   # Configuration file
├── start.sh              # Start script
├── stop.sh               # Stop script
├── skills/               # Local skills directory (example)
└── README.md             # This file
```

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

## Dependencies

- **fastmcp**: The FastMCP framework for building MCP servers
- **pydantic**: Data validation for configuration

## License

This project is provided as-is for use with FastMCP.

## Resources

- [FastMCP Documentation](https://gofastmcp.com/)
- [FastMCP Skills Provider](https://gofastmcp.com/servers/providers/skills)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review server logs in `server.log`
3. Visit [FastMCP Documentation](https://gofastmcp.com/)
4. Check [MCP Discord Community](https://discord.gg/uu8dJCgttd)
