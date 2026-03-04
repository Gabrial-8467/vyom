"""
Package manager configuration and settings.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class PackageManagerConfig:
    """Configuration for Falcon package manager."""
    
    # Directory paths
    falcon_dir: str = ".falcon"
    packages_dir: str = "packages"
    registry_file: str = "registry.json"
    config_file: str = "config.json"
    
    # Registry settings
    default_registry_url: str = "https://registry.falcon-lang.org"
    cache_expiry_hours: int = 24
    
    # Installation settings
    auto_resolve_dependencies: bool = True
    allow_prerelease: bool = False
    
    def get_falcon_dir_path(self, base_path: Optional[str] = None) -> Path:
        """Get the .falcon directory path."""
        if base_path:
            return Path(base_path) / self.falcon_dir
        return Path.cwd() / self.falcon_dir
    
    def get_packages_dir_path(self, base_path: Optional[str] = None) -> Path:
        """Get the packages directory path."""
        return self.get_falcon_dir_path(base_path) / self.packages_dir
    
    def get_registry_path(self, base_path: Optional[str] = None) -> Path:
        """Get the registry file path."""
        return self.get_falcon_dir_path(base_path) / self.registry_file
    
    def get_config_path(self, base_path: Optional[str] = None) -> Path:
        """Get the config file path."""
        return self.get_falcon_dir_path(base_path) / self.config_file
    
    def ensure_directories(self, base_path: Optional[str] = None) -> None:
        """Ensure all required directories exist."""
        falcon_dir = self.get_falcon_dir_path(base_path)
        packages_dir = self.get_packages_dir_path(base_path)
        
        falcon_dir.mkdir(exist_ok=True)
        packages_dir.mkdir(exist_ok=True)
    
    def load(self, base_path: Optional[str] = None) -> "PackageManagerConfig":
        """Load configuration from file."""
        config_path = self.get_config_path(base_path)
        
        if not config_path.exists():
            return self
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update this instance with loaded data
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    
        except (json.JSONDecodeError, IOError):
            # Use defaults if config is corrupted
            pass
        
        return self
    
    def save(self, base_path: Optional[str] = None) -> None:
        """Save configuration to file."""
        self.ensure_directories(base_path)
        config_path = self.get_config_path(base_path)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2)
