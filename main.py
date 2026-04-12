"""FastMCP Skills Provider Server

This MCP server exposes skills from configured directories as resources.
Skills are directories containing a SKILL.md file and supporting materials.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider

from config import ConfigLoader, SkillsConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SkillsProviderServer:
    """FastMCP Skills Provider Server"""
    
    def __init__(self, config_file: str = "skills.settings.json"):
        """Initialize the skills provider server
        
        Args:
            config_file: Path to configuration file
        """
        self.config_loader = ConfigLoader(config_file)
        self.mcp = FastMCP("Skills Provider")
        self._setup_providers()
    
    def _setup_providers(self):
        """Setup skills providers from configuration"""
        directories = self.config_loader.get_directories()
        reload_mode = self.config_loader.get_reload_mode()
        supporting_files = self.config_loader.get_supporting_files_mode()
        
        logger.info(f"Setting up SkillsDirectoryProvider")
        logger.info(f"  Directories: {[str(d) for d in directories]}")
        logger.info(f"  Reload mode: {reload_mode}")
        logger.info(f"  Supporting files mode: {supporting_files}")
        
        # Create skills directory provider
        provider = SkillsDirectoryProvider(
            roots=directories,
            reload=reload_mode,
            supporting_files=supporting_files
        )
        
        self.mcp.add_provider(provider)
        logger.info("SkillsDirectoryProvider added successfully")
    
    def run(self):
        """Run the MCP server"""
        logger.info("Starting FastMCP Skills Provider Server")
        try:
            self.mcp.run()
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            sys.exit(1)


def run_http_server(config_file: str, port: int):
    """Run MCP server with HTTP transport (for MCP gateway)"""
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
        import uvicorn
    except ImportError:
        logger.error("FastAPI required for HTTP mode. Install with: pip install fastapi uvicorn")
        sys.exit(1)
    
    app = FastAPI(title="FastMCP Skills Provider")
    server_instance = SkillsProviderServer(config_file)
    
    @app.on_event("startup")
    async def startup():
        logger.info(f"HTTP Server starting on http://localhost:{port}")
        logger.info("Connect your MCP gateway with transport: 'streamable-http' and url: 'http://localhost:{port}/mcp'")
    
    @app.post("/mcp")
    async def mcp_endpoint(request: Request):
        """MCP JSON-RPC endpoint for gateway communication"""
        try:
            data = await request.json()
        except Exception as e:
            logger.error(f"Failed to parse request: {e}")
            return JSONResponse(
                status_code=400,
                content={"error": {"code": -32700, "message": "Parse error"}}
            )
        
        # Handle JSON-RPC 2.0 requests
        if not isinstance(data, dict) or data.get("jsonrpc") != "2.0":
            return JSONResponse(
                status_code=400,
                content={"error": {"code": -32600, "message": "Invalid Request"}}
            )
        
        method = data.get("method", "")
        params = data.get("params", {})
        request_id = data.get("id")
        
        logger.info(f"MCP Request: {method}")
        
        try:
            # Handle different MCP methods
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "resources": {
                            "listChanged": True,
                            "subscribe": False
                        }
                    },
                    "serverInfo": {
                        "name": "Skills Provider",
                        "version": "1.0.0"
                    }
                }
            elif method == "resources/list":
                result = await handle_resources_list(server_instance)
            elif method == "resources/read":
                result = await handle_resources_read(server_instance, params)
            elif method == "tools/list":
                result = {"tools": []}  # Skills provider doesn't expose tools
            elif method == "prompts/list":
                result = {"prompts": []}  # Skills provider doesn't expose prompts
            else:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"Method not found: {method}"}
                    }
                )
            
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            )
        except Exception as e:
            logger.error(f"Error handling {method}: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32603, "message": str(e)}
                }
            )
    
    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    logger.info(f"Starting HTTP server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


async def handle_resources_list(server_instance: SkillsProviderServer) -> dict:
    """Handle resources/list MCP method"""
    resources = []
    
    # Get resources from the MCP server
    try:
        # Access the provider to get resources
        for provider in server_instance.mcp._providers:
            if hasattr(provider, 'list_resources'):
                provider_resources = await provider.list_resources() if asyncio.iscoroutinefunction(provider.list_resources) else provider.list_resources()
                if hasattr(provider_resources, '__aiter__'):
                    async for resource in provider_resources:
                        resources.append({
                            "uri": resource.uri,
                            "name": resource.name,
                            "description": resource.description or "",
                            "mimeType": resource.mimeType or "text/plain"
                        })
                elif hasattr(provider_resources, '__iter__'):
                    for resource in provider_resources:
                        resources.append({
                            "uri": resource.uri,
                            "name": resource.name,
                            "description": resource.description or "",
                            "mimeType": resource.mimeType or "text/plain"
                        })
    except Exception as e:
        logger.debug(f"Error listing resources: {e}")
    
    return {"resources": resources}


async def handle_resources_read(server_instance: SkillsProviderServer, params: dict) -> dict:
    """Handle resources/read MCP method"""
    uri = params.get("uri", "")
    
    try:
        # Access the provider to read resource
        for provider in server_instance.mcp._providers:
            if hasattr(provider, 'read_resource'):
                content = await provider.read_resource(uri) if asyncio.iscoroutinefunction(provider.read_resource) else provider.read_resource(uri)
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "text/plain",
                            "text": content if isinstance(content, str) else str(content)
                        }
                    ]
                }
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        return {"error": {"code": -32603, "message": str(e)}}
    
    return {"error": {"code": -32602, "message": f"Resource not found: {uri}"}}



def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='FastMCP Skills Provider Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Run with default stdio transport (for Cursor/Claude)
  python main.py
  
  # Run with HTTP transport (for MCP gateway)
  python main.py --http --port 3000
  
  # Run with custom configuration file
  python main.py --config /path/to/config.json
  
  # Create a default configuration file
  python main.py --init
        '''
    )
    parser.add_argument(
        '--config',
        default='skills.settings.json',
        help='Path to configuration file (default: skills.settings.json)'
    )
    parser.add_argument(
        '--init',
        action='store_true',
        help='Create a default configuration file and exit'
    )
    parser.add_argument(
        '--http',
        action='store_true',
        help='Run with HTTP transport instead of stdio (for MCP gateway)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=3000,
        help='HTTP port (default: 3000)'
    )
    
    args = parser.parse_args()
    
    if args.init:
        ConfigLoader.create_default_config(args.config)
        sys.exit(0)
    
    try:
        if args.http:
            # Run HTTP server
            run_http_server(args.config, args.port)
        else:
            # Run stdio server
            server = SkillsProviderServer(args.config)
            server.run()
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        logger.info("Hint: Run 'python main.py --init' to create a default configuration")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
