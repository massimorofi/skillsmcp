"""FastMCP Skills Provider Server"""

import asyncio
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx
from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider

from config import ConfigLoader

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SkillsProviderServer:
    """FastMCP Skills Provider Server"""

    def __init__(self, config_file: str = "skills.settings.json"):
        self.config_loader = ConfigLoader(config_file)
        self.mcp = FastMCP("Skills Provider")
        self._setup_providers()

    def _setup_providers(self):
        directories = self.config_loader.get_directories()
        reload_mode = self.config_loader.get_reload_mode()
        supporting_files = self.config_loader.get_supporting_files_mode()

        logger.info(f"Setting up SkillsDirectoryProvider")
        logger.info(f"  Directories: {[str(d) for d in directories]}")
        logger.info(f"  Reload mode: {reload_mode}")
        logger.info(f"  Supporting files mode: {supporting_files}")

        provider = SkillsDirectoryProvider(
            roots=directories, reload=reload_mode, supporting_files=supporting_files
        )

        self.mcp.add_provider(provider)
        logger.info("SkillsDirectoryProvider added successfully")
        self._setup_tools(provider)

    def _setup_tools(self, provider):
        @self.mcp.tool()
        async def list_skills() -> List[Dict[str, str]]:
            """List all available skills

            Returns a list of all skills that are available in the configured directories.
            """
            resources = await provider.list_resources()
            skills = {}
            res_list = list(resources) if hasattr(resources, "__iter__") else []
            for r in res_list:
                uri = str(r.uri)
                if uri.endswith("/SKILL.md"):
                    skill_name = uri.split("skill://")[1].split("/")[0]
                    skills[skill_name] = r.description or f"Skill: {skill_name}"
            return [{"name": n, "description": d} for n, d in skills.items()]

        @self.mcp.tool()
        async def get_skill(skill_name: str) -> str:
            """Get skill content by name"""
            uri = f"skill://{skill_name}/SKILL.md"
            try:
                resource = await provider.get_resource(uri)
                if hasattr(resource, "read"):
                    content = await resource.read()
                    return content if content else f"Skill {skill_name} not found"
                return str(resource)
            except Exception as e:
                return f"Error: {str(e)}"

        @self.mcp.tool()
        async def list_skill_files(skill_name: str) -> List[str]:
            """List all files in a skill

            Returns all files associated with a specific skill.

            Args:
                skill_name: The name of the skill
            """
            resources = await provider.list_resources()
            files = []
            res_list = list(resources) if hasattr(resources, "__iter__") else []
            for r in res_list:
                uri = str(r.uri)
                if uri.startswith(f"skill://{skill_name}/"):
                    files.append(uri.split(f"skill://{skill_name}/")[1])
            return files

        logger.info("Skills tools added successfully")
        logger.info(f"Registered tools: list_skills, get_skill, list_skill_files")

    def run(self):
        logger.info("Starting FastMCP Skills Provider Server")
        try:
            self.mcp.run()
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            sys.exit(1)


def run_http_server(config_file: str, port: int, gateway_url: str = None):
    """Run MCP server with HTTP transport for gateway"""
    server_instance = SkillsProviderServer(config_file)

    logger.info(f"Starting FastMCP Skills Provider with sse transport")
    logger.info(f"Port: {port}")
    logger.info(f"Endpoint: http://localhost:{port}/sse")
    logger.info(f"Tools configured:")
    logger.info(f"  - list_skills: List all available skills")
    logger.info(f"  - get_skill: Get skill content by name")
    logger.info(f"  - list_skill_files: List all files in a skill")
    logger.info(
        f"Register with gateway: transport=streamable-http, url=http://localhost:{port}/mcp"
    )

    # Start heartbeat thread to keep server visible to gateway
    config_loader = ConfigLoader(config_file)
    gateway_config = config_loader.get_gateway_config()
    if gateway_config.enabled:
        gateway_host = gateway_config.host or "localhost"
        gateway_port = gateway_config.port or 8000
        server_name = gateway_config.name or "skills-provider"

        def heartbeat_loop():
            """Send periodic heartbeats to the gateway"""
            gateway_url = f"http://{gateway_host}:{gateway_port}/heartbeat"
            while True:
                try:
                    # Send heartbeat every 15 seconds (well under 30 second timeout)
                    response = httpx.get(
                        gateway_url, params={"server_name": server_name}, timeout=5.0
                    )
                    if response.status_code == 200:
                        logger.debug(f"Heartbeat sent to gateway ({server_name})")
                    else:
                        logger.warning(
                            f"Gateway heartbeat failed: {response.status_code}"
                        )
                except Exception as e:
                    logger.warning(f"Heartbeat error: {e}")
                finally:
                    time.sleep(15)  # Send heartbeat every 15 seconds

        # Start heartbeat thread as daemon so it doesn't block server shutdown
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        logger.info(
            f"Heartbeat thread started (gateway: {gateway_host}:{gateway_port}, server: {server_name})"
        )

    # Use streamable-http transport which is compatible with MCP gateways
    server_instance.mcp.run(transport="streamable-http", host="0.0.0.0", port=port)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="FastMCP Skills Provider Server")
    parser.add_argument("--config", default="skills.settings.json")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--http", action="store_true")
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    if args.init:
        ConfigLoader.create_default_config(args.config)
        sys.exit(0)

    try:
        config_loader = ConfigLoader(args.config)
        use_http = args.http
        if not use_http and config_loader.get_gateway_config().enabled:
            logger.info("Gateway enabled in config - switching to HTTP transport")
            use_http = True

        # Use provided port or fall back to config port
        http_port = args.port or config_loader.get_http_config().port

        if use_http:
            run_http_server(args.config, http_port)
        else:
            server = SkillsProviderServer(args.config)
            server.run()
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
