---
description: Example skill demonstrating the FastMCP Skills Provider
---

# Example Skill

This is an example skill that demonstrates the structure and format for skills in the FastMCP Skills Provider.

## Overview

Skills are directories containing a `SKILL.md` file (main instructions) and optional supporting files. This example shows how to structure a skill properly.

## Key Features

- **Metadata**: YAML frontmatter with description
- **Main Content**: Clear documentation of the skill's purpose
- **Supporting Files**: Can include additional documentation and resources
- **Discoverable**: Automatically discovered by the FastMCP Skills Provider

## Usage

When this skill is loaded by the FastMCP Skills Provider, clients can:

1. **List** available skills using the MCP client
2. **Read** the main `SKILL.md` file
3. **Download** supporting files
4. **Access** the manifest to see all files in the skill

## Creating Your Own Skills

To create a new skill:

1. Create a directory with your skill name (e.g., `my-skill`)
2. Add a `SKILL.md` file with at least a title or description
3. Optional: Add supporting files (e.g., `reference.md`, `examples/`)
4. Place the directory in a configured skill directory
5. If reload mode is enabled, it will be discovered immediately; otherwise, restart the server

## Skill Structure Template

```
my-skill/
├── SKILL.md              # Main instructions
├── reference.md          # Optional reference
├── examples/
│   ├── example1.md
│   └── example2.md
└── data/
    └── sample-data.json
```

## Resources

- [FastMCP Skills Provider](https://gofastmcp.com/servers/providers/skills)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)

---

**Note**: This is an example skill. Replace it with your own skills by following the structure above.
