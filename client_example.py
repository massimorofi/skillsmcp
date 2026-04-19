#!/usr/bin/env python3
"""
Example FastMCP Skills Provider Client

This script demonstrates how to interact with the FastMCP Skills Provider server.
It shows how to:
- List available skills
- Read skill contents
- Download skills
- Inspect skill manifests

Usage:
  python client_example.py
  python client_example.py list
  python client_example.py read example-skill
  python client_example.py download example-skill ~/.claude/skills
"""

import asyncio
import sys
from pathlib import Path

try:
    from fastmcp import Client
    from fastmcp.utilities.skills import (
        list_skills,
        get_skill_manifest,
        download_skill,
        sync_skills
    )
except ImportError:
    print("Error: FastMCP not installed")
    print("Run: pip install fastmcp")
    sys.exit(1)


async def list_available_skills(server_url: str = "http://localhost:3001/mcp"):
    """List all available skills on the server"""
    print(f"Connecting to {server_url}...")
    
    try:
        async with Client(server_url) as client:
            print("\nFetching available skills...\n")
            skills = await list_skills(client)
            
            if not skills:
                print("No skills found on the server.")
                return
            
            print(f"Found {len(skills)} skill(s):\n")
            for skill in skills:
                print(f"  📚 {skill.name}")
                if skill.description:
                    print(f"     {skill.description}")
                print()
    except Exception as e:
        print(f"Error connecting to server: {e}")
        print("Make sure the server is running: ./start.sh")
        sys.exit(1)


async def read_skill(skill_name: str, server_url: str = "http://localhost:5000/mcp"):
    """Read a specific skill's SKILL.md file"""
    print(f"Connecting to {server_url}...")
    
    try:
        async with Client(server_url) as client:
            uri = f"skill://{skill_name}/SKILL.md"
            print(f"\nReading: {uri}\n")
            
            result = await client.read_resource(uri)
            print(result[0].text)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


async def show_manifest(skill_name: str, server_url: str = "http://localhost:5000/mcp"):
    """Show the manifest (file listing) for a skill"""
    print(f"Connecting to {server_url}...")
    
    try:
        async with Client(server_url) as client:
            print(f"\nFetching manifest for '{skill_name}'...\n")
            
            manifest = await get_skill_manifest(client, skill_name)
            
            print(f"Skill: {manifest.skill}")
            print(f"Files:\n")
            
            for file_info in manifest.files:
                size_kb = file_info.size / 1024
                print(f"  📄 {file_info.path}")
                print(f"     Size: {size_kb:.1f} KB")
                print(f"     Hash: {file_info.hash}")
                print()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


async def download_single_skill(
    skill_name: str,
    destination: str = None,
    server_url: str = "http://localhost:5000/mcp"
):
    """Download a single skill from the server"""
    if destination is None:
        destination = str(Path.home() / ".claude" / "skills")
    
    dest_path = Path(destination)
    print(f"Connecting to {server_url}...")
    print(f"Downloading '{skill_name}' to {dest_path}...\n")
    
    try:
        async with Client(server_url) as client:
            path = await download_skill(client, skill_name, dest_path)
            print(f"✓ Downloaded to: {path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


async def download_all_skills(
    destination: str = None,
    server_url: str = "http://localhost:5000/mcp"
):
    """Download all skills from the server"""
    if destination is None:
        destination = str(Path.home() / ".claude" / "skills")
    
    dest_path = Path(destination)
    print(f"Connecting to {server_url}...")
    print(f"Downloading all skills to {dest_path}...\n")
    
    try:
        async with Client(server_url) as client:
            paths = await sync_skills(client, dest_path)
            
            print(f"\n✓ Downloaded {len(paths)} skill(s):")
            for path in paths:
                print(f"  - {path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def print_usage():
    """Print usage information"""
    print("""
FastMCP Skills Provider Client

Usage:
  python client_example.py [COMMAND] [ARGS]

Commands:
  list                              List all available skills
  read <skill-name>                 Read a skill's SKILL.md file
  manifest <skill-name>             Show skill manifest (files and hashes)
  download <skill-name> [DEST]      Download a specific skill
  sync [DEST]                       Download all skills
  
Arguments:
  <skill-name>   Name of the skill (e.g., 'example-skill')
  [DEST]         Destination directory (default: ~/.claude/skills)

Examples:
  # List all skills
  python client_example.py list
  
  # Read a specific skill
  python client_example.py read example-skill
  
  # Show a skill's files
  python client_example.py manifest example-skill
  
  # Download a skill
  python client_example.py download example-skill
  
  # Download all skills to a custom location
  python client_example.py sync ~/my-skills
  
  # Download a skill to a custom location
  python client_example.py download example-skill ~/my-skills

Default server URL: http://localhost:5000/mcp

Make sure the FastMCP Skills Provider server is running before using this client:
  ./start.sh
    """)


async def main():
    """Main entry point"""
    if len(sys.argv) < 2 or sys.argv[1] in ("help", "--help", "-h"):
        print_usage()
        return
    
    command = sys.argv[1]
    
    if command == "list":
        await list_available_skills()
    
    elif command == "read":
        if len(sys.argv) < 3:
            print("Error: skill name required")
            print("Usage: python client_example.py read <skill-name>")
            sys.exit(1)
        await read_skill(sys.argv[2])
    
    elif command == "manifest":
        if len(sys.argv) < 3:
            print("Error: skill name required")
            print("Usage: python client_example.py manifest <skill-name>")
            sys.exit(1)
        await show_manifest(sys.argv[2])
    
    elif command == "download":
        if len(sys.argv) < 3:
            print("Error: skill name required")
            print("Usage: python client_example.py download <skill-name> [destination]")
            sys.exit(1)
        dest = sys.argv[3] if len(sys.argv) > 3 else None
        await download_single_skill(sys.argv[2], dest)
    
    elif command == "sync":
        dest = sys.argv[2] if len(sys.argv) > 2 else None
        await download_all_skills(dest)
    
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
