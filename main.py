"""FastMCP Skills Provider Server

This MCP server exposes skills from configured directories as resources.
Skills are directories containing a SKILL.md file and supporting materials.
"""

import asyncio
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
        main_file = self.config_loader.get_main_file()
        
        logger.info(f"Setting up SkillsDirectoryProvider")
        logger.info(f"  Directories: {[str(d) for d in directories]}")
        logger.info(f"  Reload mode: {reload_mode}")
        logger.info(f"  Supporting files mode: {supporting_files}")
        logger.info(f"  Main file: {main_file}")
        
        # Create skills directory provider
        provider = SkillsDirectoryProvider(
            roots=directories,
            reload=reload_mode,
            supporting_files=supporting_files,
            main_file=main_file
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


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='FastMCP Skills Provider Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Run with default configuration file
  python main.py
  
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
    
    args = parser.parse_args()
    
    if args.init:
        ConfigLoader.create_default_config(args.config)
        sys.exit(0)
    
    try:
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
