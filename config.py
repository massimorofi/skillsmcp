"""Configuration handler for FastMCP Skills Provider"""

import json
from pathlib import Path
from typing import List
from pydantic import BaseModel, field_validator


class SkillsConfig(BaseModel):
    """Configuration model for skills provider"""
    
    directories: List[str]
    reload: bool = False
    supporting_files: str = "template"  # "template" or "resources"
    main_file: str = "SKILL.md"
    
    @field_validator('directories')
    @classmethod
    def validate_directories(cls, v):
        """Ensure directories list is not empty"""
        if not v:
            raise ValueError("At least one directory must be specified")
        return v
    
    @field_validator('supporting_files')
    @classmethod
    def validate_supporting_files(cls, v):
        """Validate supporting_files mode"""
        if v not in ("template", "resources"):
            raise ValueError("supporting_files must be 'template' or 'resources'")
        return v


class ConfigLoader:
    """Loads and manages skills configuration"""
    
    def __init__(self, config_file: str = "skills.settings.json"):
        self.config_file = Path(config_file)
        self.config: SkillsConfig = self._load_config()
    
    def _load_config(self) -> SkillsConfig:
        """Load configuration from JSON file"""
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Configuration file '{self.config_file}' not found. "
                "Please create it with at least one skills directory."
            )
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            return SkillsConfig(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}")
    
    def get_directories(self) -> List[Path]:
        """Get skill directories as Path objects, expanding ~ and resolving to absolute paths"""
        return [Path(d).expanduser().resolve() for d in self.config.directories]
    
    def get_reload_mode(self) -> bool:
        """Get reload mode setting"""
        return self.config.reload
    
    def get_supporting_files_mode(self) -> str:
        """Get supporting files mode"""
        return self.config.supporting_files
    
    def get_main_file(self) -> str:
        """Get main file name"""
        return self.config.main_file
    
    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()
        print("Configuration reloaded")
    
    @staticmethod
    def create_default_config(config_file: str = "skills.settings.json"):
        """Create a default configuration file"""
        default_config = {
            "directories": [
                str(Path.home() / ".claude" / "skills"),
                "./skills"
            ],
            "reload": False,
            "supporting_files": "template",
            "main_file": "SKILL.md"
        }
        
        config_path = Path(config_file)
        if config_path.exists():
            print(f"Configuration file '{config_file}' already exists")
            return False
        
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"Created default configuration file: {config_file}")
        return True
