# FastMCP Skills Provider - Architecture & Design

## System Architecture

```
┌─────────────────────────────────────────┐
│      MCP Clients                        │
│  (Claude, Cursor, VS Code, etc.)        │
└────────────────┬────────────────────────┘
                 │
                 │ MCP Protocol
                 │ (HTTP/WebSocket)
                 ▼
┌─────────────────────────────────────────┐
│   FastMCP Server (main.py)               │
│  ┌───────────────────────────────────┐  │
│  │ SkillsDirectoryProvider           │  │
│  │  - Scans skill directories        │  │
│  │  - Creates skill resources        │  │
│  │  - Handles resource requests      │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ ConfigLoader (config.py)          │  │
│  │  - Loads skills.settings.json     │  │
│  │  - Manages configuration          │  │
│  │  - Validates settings             │  │
│  └───────────────────────────────────┘  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│     Skill Directories                   │
│  ┌──────────────┐  ┌──────────────────┐ │
│  │  ~/.claude/  │  │  ~/.cursor/      │ │
│  │  skills/     │  │  skills/         │ │
│  │              │  │                  │ │
│  │ ├─example-   │  │ ├─skill1/        │ │
│  │ │ skill/     │  │ │ └─SKILL.md     │ │
│  │ │ ├─SKILL.md │  │ └─skill2/        │ │
│  │ │ └─...      │  │   └─SKILL.md     │ │
│  │ └─...        │  └──────────────────┘ │
│  │              │  ┌──────────────────┐ │
│  │              │  │  ./skills/       │ │
│  │              │  │  (local)         │ │
│  │              │  │                  │ │
│  │              │  │ ├─docs-skill/    │ │
│  │              │  │ │ └─SKILL.md     │ │
│  │              │  │ └─...            │ │
│  │              │  └──────────────────┘ │
│  └──────────────┘                       │
└─────────────────────────────────────────┘
```

### Components

#### 1. FastMCP Server (main.py)
- Entry point for the MCP application
- Creates FastMCP instance and adds SkillsDirectoryProvider
- Handles MCP protocol communication
- Lifecycle management

#### 2. SkillsDirectoryProvider (from FastMCP)
- Scans configured directories for skills
- Creates skill resources with `skill://` URIs
- Handles resource listing and reading
- Optional reload mode for development

#### 3. ConfigLoader (config.py)
- Loads and validates `skills.settings.json`
- Manages configuration state
- Provides configuration accessors
- Supports configuration reloading

#### 4. Skill Directories
- User-configured directories containing skills
- Each skill is a subdirectory with `SKILL.md`
- Supporting files stored alongside main file

## Data Flow

### Skill Discovery (on server start)

```
skills.settings.json
        ↓
  ConfigLoader
        ↓
  Validate configuration
        ↓
  Read directories from config
        ↓
  SkillsDirectoryProvider
        ↓
  Scan each directory
        ↓
  For each subdirectory with SKILL.md:
    - Parse metadata from frontmatter
    - Index supporting files
    - Create resource URIs
        ↓
  Skills registered and ready to serve
```

### Resource Request (when client requests skill)

```
Client Request
  skill://example-skill/SKILL.md
        ↓
  FastMCP receives request
        ↓
  SkillsDirectoryProvider.read_resource()
        ↓
  Locate skill directory
        ↓
  Read requested file
        ↓
  Return content to client
```

## Configuration

### File: skills.settings.json

```json
{
  "directories": [
    "~/.claude/skills",
    "./skills",
    "/app/skills"
  ],
  "reload": false,
  "supporting_files": "template",
  "main_file": "SKILL.md"
}
```

### Configuration Validation (Pydantic)

```python
SkillsConfig(BaseModel):
  directories: List[str]          # Required, non-empty
  reload: bool                    # Optional, default False
  supporting_files: str           # Optional, "template" or "resources"
  main_file: str                  # Optional, default "SKILL.md"
```

## Skill Structure

### Directory Layout

```
skill-name/
├── SKILL.md              # Main instruction file (required)
├── reference.md          # Supporting documentation (optional)
├── examples/             # Examples directory (optional)
│   ├── example1.md
│   └── config.json
└── data/                 # Data directory (optional)
    └── sample.json
```

### SKILL.md Format

```markdown
---
description: One-line description of skill
metadata-field: value
---

# Skill Title

Skill content...
```

## Resource URIs

FastMCP skills expose three resource types:

### 1. Main Instruction File
```
skill://skill-name/SKILL.md
```
- Contains main skill instructions
- Parsed for YAML frontmatter metadata
- Required for skill to be discoverable

### 2. Manifest
```
skill://skill-name/_manifest
```
- Synthetic JSON resource
- Lists all files in skill directory
- Includes file sizes and SHA256 hashes
- Used for integrity verification

### 3. Supporting Files
```
skill://skill-name/path/to/file
```
- Any file within the skill directory
- Accessible by relative path
- Listed in manifest

## Operating Modes

### Template Mode (Default)
- Supporting files not listed by `list_resources()`
- Clients discover files through manifest
- Keeps resource list compact
- Efficient for skills with many files

### Resources Mode
- All files appear as individual resources
- Full enumeration in `list_resources()`
- No need to read manifest first
- Better for small skills or full discovery

### Reload Mode
- Director rescanned on each request
- Changes to skills appear immediately
- Overhead added to every request
- Recommended for development only
- Disable in production for performance

## Deployment

### Single Instance
```bash
./start.sh
# Server listens on default FastMCP port
# One server instance handles all requests
```

### Multiple Instances
```bash
# Instance 1 (local skills)
python main.py --config config-local.json

# Instance 2 (shared skills)  
python main.py --config config-shared.json

# Clients connect to specific instances
```

### With Load Balancer
```
              ┌──────────────────────┐
              │   Load Balancer      │
              └──────────┬───────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │ Server1 │      │ Server2 │      │ Server3 │
   │ :5000   │      │ :5001   │      │ :5002   │
   └─────────┘      └─────────┘      └─────────┘
        ▼                ▼                ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │ skills/ │      │ skills/ │      │ skills/ │
   │ (local) │      │ (shared)│      │ (cloud) │
   └─────────┘      └─────────┘      └─────────┘
```

## Development Workflow

### 1. Setup Development Environment
```bash
./setup.sh                    # Creates venv and installs dependencies
python main.py --init        # Creates default configuration
```

### 2. Edit Configuration
```bash
# Enable reload mode for development
# Edit skills.settings.json:
{
  "reload": true,
  "directories": ["./skills", "~/.claude/skills"]
}
```

### 3. Start Server with Live Reload
```bash
./start.sh                # Start server with reload mode enabled
```

### 4. Add/Edit Skills
```bash
# Edit existing skill
vim ./skills/example-skill/SKILL.md

# Add new skill
mkdir ./skills/new-skill
echo "# New Skill" > ./skills/new-skill/SKILL.md

# Changes appear immediately in clients
```

### 5. Test with Client
```bash
python client_example.py list          # List skills
python client_example.py read example-skill    # Read skill
```

### 6. Disable Reload for Production
```bash
# Edit skills.settings.json:
{
  "reload": false
}

# Restart server
./stop.sh
./start.sh
```

## Performance Considerations

### Optimization Tips

| Factor | Optimization |
|--------|--------------|
| Directory Size | Split into multiple roots, use reload=false |
| File Count | Use template mode for many supporting files |
| Skill Count | Consider sharding across servers |
| Network Latency | Deploy server closer to clients |
| RAM Usage | Disable reload mode in production |

### Scaling Strategies

1. **Horizontal Scaling**: Multiple server instances
2. **Directory Sharding**: Split skills across directories
3. **Caching**: Client-side caching of skill resources
4. **Compression**: HTTP compression for resource delivery
5. **CDN**: Distribute skills via CDN for read-heavy access

## Error Handling

### Configuration Errors
- Invalid JSON in skills.settings.json
- Missing required directories
- Invalid configuration values
- Invalid path syntax

### Runtime Errors
- Directory access denied
- Corrupted SKILL.md files
- Missing main instruction file
- File read errors

### Client Errors
- Invalid resource URIs
- Requesting non-existent skills
- Protocol violations

## Security Considerations

1. **Directory Permissions**: Restrict access to skill directories
2. **File Permissions**: Skills should have appropriate read permissions
3. **Frontmatter Injection**: Validate YAML frontmatter parsing
4. **Path Traversal**: Verify paths don't escape skill directories
5. **Access Control**: Consider implementing authentication if needed

## Extensibility

### Adding Custom Providers
```python
from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider

mcp = FastMCP("Custom Skills")

# Add multiple providers
mcp.add_provider(SkillsDirectoryProvider(roots=local_roots))
mcp.add_provider(SkillsDirectoryProvider(roots=shared_roots))
```

### Custom Configuration
Extend ConfigLoader for additional settings:
```python
class ExtendedConfig(SkillsConfig):
    webhook_url: str = None
    auth_token: str = None
```

### Monitoring and Logging
- FastMCP provides comprehensive logging
- Configure log levels in config
- Monitor skill discovery performance
- Track client requests

## Future Enhancements

1. **Skill Dependencies**: Declare dependencies between skills
2. **Versioning**: Support multiple versions of same skill
3. **Validation**: Automated skill format validation
4. **Publishing**: Central skill repository/marketplace
5. **Signing**: Cryptographic signing for skill verification
6. **Caching**: Server-side caching for expensive operations
7. **Metrics**: Prometheus metrics for monitoring
8. **GraphQL API**: Additional query interface

## References

- [FastMCP Documentation](https://gofastmcp.com/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
