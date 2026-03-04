"""
Main package manager interface.
"""

from pathlib import Path
from typing import List, Optional, Dict, Tuple

from .config import PackageManagerConfig
from .package import Package, PackageMetadata
from .installer import PackageInstaller
from .resolver import DependencyResolver, DependencyConflict


class PackageManager:
    """Main interface for Falcon package management."""
    
    def __init__(self, base_path: Optional[str] = None):
        self.config = PackageManagerConfig().load(base_path)
        self.installer = PackageInstaller(self.config)
        self._installed_packages_cache: Optional[Dict[str, Package]] = None
    
    @property
    def installed_packages(self) -> Dict[str, Package]:
        """Get all installed packages (cached)."""
        if self._installed_packages_cache is None:
            self._refresh_package_cache()
        return self._installed_packages_cache or {}
    
    def _refresh_package_cache(self) -> None:
        """Refresh the installed packages cache."""
        self._installed_packages_cache = {}
        for package in self.installer.list_installed_packages():
            self._installed_packages_cache[package.name] = package
    
    def install_package(self, source: str) -> Tuple[bool, str]:
        """
        Install a package from various sources.
        
        Args:
            source: Path to directory, archive file, or URL
            
        Returns:
            Tuple of (success, message)
        """
        try:
            source_path = Path(source)
            
            if source_path.is_dir():
                # Install from directory
                package = self.installer.install_from_directory(source_path)
            elif source_path.is_file():
                # Install from archive
                package = self.installer.install_from_archive(source_path)
            elif source.startswith(('http://', 'https://')):
                # Install from URL
                package = self.installer.install_from_url(source)
            else:
                return False, f"Invalid package source: {source}"
            
            # Refresh cache
            self._refresh_package_cache()
            
            return True, f"Successfully installed {package.name} v{package.version}"
            
        except Exception as e:
            return False, f"Failed to install package: {str(e)}"
    
    def uninstall_package(self, package_name: str) -> Tuple[bool, str]:
        """
        Uninstall a package.
        
        Args:
            package_name: Name of the package to uninstall
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.installer.is_installed(package_name):
                return False, f"Package '{package_name}' is not installed"
            
            # Check for dependent packages
            dependents = self._find_dependent_packages(package_name)
            if dependents:
                return False, f"Cannot uninstall '{package_name}'. Required by: {', '.join(dependents)}"
            
            success = self.installer.uninstall(package_name)
            if success:
                self._refresh_package_cache()
                return True, f"Successfully uninstalled '{package_name}'"
            else:
                return False, f"Failed to uninstall '{package_name}'"
                
        except Exception as e:
            return False, f"Failed to uninstall package: {str(e)}"
    
    def list_packages(self) -> List[Package]:
        """List all installed packages."""
        return list(self.installed_packages.values())
    
    def get_package(self, package_name: str) -> Optional[Package]:
        """Get an installed package by name."""
        return self.installed_packages.get(package_name)
    
    def search_packages(self, query: str) -> List[Package]:
        """Search installed packages by name or description."""
        results = []
        query_lower = query.lower()
        
        for package in self.installed_packages.values():
            if (query_lower in package.name.lower() or 
                query_lower in package.metadata.description.lower()):
                results.append(package)
        
        return results
    
    def check_dependencies(self, package_name: str) -> Tuple[List[str], List[DependencyConflict]]:
        """
        Check dependencies for a package.
        
        Returns:
            Tuple of (satisfied_dependencies, conflicts)
        """
        package = self.get_package(package_name)
        if not package:
            return [], []
        
        resolver = DependencyResolver(self.installed_packages)
        resolved, conflicts = resolver.resolve_dependencies(package)
        
        satisfied = [pkg.name for pkg in resolved]
        return satisfied, conflicts
    
    def create_package(self, directory: Path, metadata: PackageMetadata) -> Tuple[bool, str]:
        """
        Create a new package in the specified directory.
        
        Args:
            directory: Directory to create package in
            metadata: Package metadata
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create package structure
            package_dir = directory / metadata.name
            lib_dir = package_dir / "lib"
            
            package_dir.mkdir(exist_ok=True)
            lib_dir.mkdir(exist_ok=True)
            
            # Save metadata
            package = Package(metadata=metadata, root_path=package_dir)
            package.save_metadata()
            
            return True, f"Package '{metadata.name}' created successfully"
            
        except Exception as e:
            return False, f"Failed to create package: {str(e)}"
    
    def get_package_info(self, package_name: str) -> Optional[Dict[str, str]]:
        """Get detailed information about a package."""
        package = self.get_package(package_name)
        if not package:
            return None
        
        return {
            "name": package.name,
            "version": package.version,
            "description": package.metadata.description,
            "author": package.metadata.author or "Unknown",
            "license": package.metadata.license or "Unspecified",
            "homepage": package.metadata.homepage or "",
            "repository": package.metadata.repository or "",
            "dependencies": ", ".join(
                f"{name}@{version}" 
                for name, version in package.metadata.dependencies.items()
            ) or "None",
            "exports": ", ".join(package.metadata.exports) or "None",
            "main": package.metadata.main or "None"
        }
    
    def _find_dependent_packages(self, package_name: str) -> List[str]:
        """Find packages that depend on the given package."""
        dependents = []
        
        for pkg in self.installed_packages.values():
            if package_name in pkg.metadata.dependencies:
                dependents.append(pkg.name)
        
        return dependents
