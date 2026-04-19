#!/usr/bin/env python3
"""Test MCP tools discovery"""

import asyncio
import json
import sys
from pathlib import Path

try:
    from fastmcp import Client
except ImportError:
    print("Error: FastMCP not installed")
    sys.exit(1)


async def test_tools():
    """Test tools/list MCP method"""
    # Connect to local MCP server via SSE
    url = "http://localhost:3001/mcp"

    print(f"Connecting to MCP server at {url}...")

    try:
        async with Client(url) as client:
            print("Connected!")

            # Call tools/list
            print("\nCalling tools/list...")
            result = await client.call_tool("list_skills", {})
            print(f"Result: {result}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_tools())
