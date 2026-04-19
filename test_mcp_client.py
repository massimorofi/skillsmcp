#!/usr/bin/env python3
"""Direct MCP Protocol test - query server via SSE"""

import asyncio
import json
from pathlib import Path


async def test_mcp():
    """Test MCP protocol communication directly"""
    try:
        from fastmcp import Client

        print("Testing MCP endpoint connection...")
        async with Client("http://localhost:3001/mcp") as client:
            print("✓ Connected to server")

            # Try to call tools/list via MCP protocol
            response = await client.call_tool("list_skills", {})
            print(f"\n✓ Tool response received:")
            print(f"  Type: {type(response).__name__}")
            if hasattr(response, "content"):
                for content in response.content:
                    print(
                        f"  Content: {content.text if hasattr(content, 'text') else content}"
                    )
            else:
                print(f"  Content: {response}")

    except ImportError:
        print("FastMCP Client not available")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp())
