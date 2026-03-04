"""
Package installation and management.
"""

import json
import shutil
import zipfile
import tarfile
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

from .package import Package, PackageMetadata
from .config import PackageManagerConfig


class PackageInstaller:
    """Handles package installation and removal."""
    
    def __init__(self, config: PackageManagerConfig):
        self.config = config
        self.config.ensure_directories()
    
    def install_from_directory(self, source_dir: Path) -> Package:
        """Install a package from a local directory."""
        if not source_dir.exists():
            raise ValueError(f"Source directory does not exist: {source_dir}")
        
        # Load package metadata
        package = Package.load_from_directory(source_dir)
        
        # Check if package is already installed
        installed_path = self.config.get_packages_dir_path() / package.name
        if installed_path.exists():
            raise ValueError(f"Package '{package.name}' is already installed")
        
        # Copy package to installation directory
        shutil.copytree(source_dir, installed_path, dirs_exist_ok=False)
        
        # Load installed package
        installed_package = Package.load_from_directory(installed_path)
        
        # Update registry
        self._update_registry(installed_package)
        
        return installed_package
    
    def install_from_archive(self, archive_path: Path) -> Package:
        """Install a package from an archive (.zip, .tar.gz)."""
        # Create temporary extraction directory
        temp_dir = self.config.get_falcon_dir_path() / "temp_install"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Extract archive
            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            elif archive_path.suffix in [".tar", ".gz"]:
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(temp_dir)
            else:
                raise ValueError(f"Unsupported archive format: {archive_path.suffix}")
            
            # Find package directory (should contain falcon.pkg)
            package_dir = None
            for item in temp_dir.iterdir():
                if (item / "falcon.pkg").exists():
                    package_dir = item
                    break
            
            if not package_dir:
                raise ValueError("Archive does not contain a valid Falcon package")
            
            # Install from extracted directory
            return self.install_from_directory(package_dir)
            
        finally:
            # Clean up temporary directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def install_from_url(self, url: str) -> Package:
        """Install a package from a URL."""
        # Download file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Determine filename from URL
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        
        if not filename:
            filename = "package.tar.gz"
        
        # Download to temporary file
        temp_file = self.config.get_falcon_dir_path() / filename
        try:
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Install from downloaded file
            return self.install_from_archive(temp_file)
            
        finally:
            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()
    
    def uninstall(self, package_name: str) -> bool:
        """Uninstall a package."""
        package_path = self.config.get_packages_dir_path() / package_name
        
        if not package_path.exists():
            return False
        
        # Remove package directory
        shutil.rmtree(package_path)
        
        # Update registry
        self._remove_from_registry(package_name)
        
        return True
    
    def is_installed(self, package_name: str) -> bool:
        """Check if a package is installed."""
        package_path = self.config.get_packages_dir_path() / package_name
        return package_path.exists()
    
    def get_installed_package(self, package_name: str) -> Optional[Package]:
        """Get an installed package."""
        if not self.is_installed(package_name):
            return None
        
        package_path = self.config.get_packages_dir_path() / package_name
        return Package.load_from_directory(package_path)
    
    def list_installed_packages(self) -> List[Package]:
        """List all installed packages."""
        packages_dir = self.config.get_packages_dir_path()
        packages = []
        
        for package_dir in packages_dir.iterdir():
            if package_dir.is_dir():
                try:
                    package = Package.load_from_directory(package_dir)
                    packages.append(package)
                except Exception:
                    # Skip invalid packages
                    continue
        
        return packages
    
    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        """Load the package registry."""
        registry_path = self.config.get_registry_path()
        
        if not registry_path.exists():
            return {}
        
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_registry(self, registry: Dict[str, Dict[str, Any]]) -> None:
        """Save the package registry."""
        registry_path = self.config.get_registry_path()
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)
    
    def _update_registry(self, package: Package) -> None:
        """Update registry with package information."""
        registry = self._load_registry()
        
        registry[package.name] = {
            "version": package.version,
            "description": package.metadata.description,
            "author": package.metadata.author,
            "installed_at": str(Path().absolute()),
            "checksum": package.calculate_checksum()
        }
        
        self._save_registry(registry)
    
    def _remove_from_registry(self, package_name: str) -> None:
        """Remove package from registry."""
        registry = self._load_registry()
        
        if package_name in registry:
            del registry[package_name]
            self._save_registry(registry)
