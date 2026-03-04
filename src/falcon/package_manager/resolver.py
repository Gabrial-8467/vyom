"""
Dependency resolution for Falcon packages.
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

from .package import Package, PackageMetadata


@dataclass
class DependencyConflict:
    """Represents a dependency conflict."""
    package: str
    requested_version: str
    installed_version: Optional[str]
    conflict_type: str  # "version_conflict", "missing", "circular"


class DependencyResolver:
    """Resolves package dependencies and detects conflicts."""
    
    def __init__(self, installed_packages: Dict[str, Package]):
        self.installed_packages = installed_packages
    
    def resolve_dependencies(self, package: Package) -> Tuple[List[Package], List[DependencyConflict]]:
        """
        Resolve dependencies for a package.
        
        Returns:
            Tuple of (resolved_packages, conflicts)
        """
        resolved = []
        conflicts = []
        visited = set()
        
        def resolve_recursive(pkg: Package, depth: int = 0) -> None:
            """Recursively resolve dependencies."""
            if depth > 50:  # Prevent infinite recursion
                conflicts.append(DependencyConflict(
                    package=pkg.name,
                    requested_version="*",
                    installed_version=None,
                    conflict_type="circular"
                ))
                return
            
            if pkg.name in visited:
                return
            
            visited.add(pkg.name)
            
            # Check each dependency
            for dep_name, version_constraint in pkg.metadata.dependencies.items():
                # Check if dependency is already installed
                if dep_name in self.installed_packages:
                    installed_pkg = self.installed_packages[dep_name]
                    
                    # Check version compatibility
                    if not self._check_version_compatibility(
                        installed_pkg.version, version_constraint
                    ):
                        conflicts.append(DependencyConflict(
                            package=dep_name,
                            requested_version=version_constraint,
                            installed_version=installed_pkg.version,
                            conflict_type="version_conflict"
                        ))
                        continue
                    
                    # Add to resolved if not already there
                    if installed_pkg not in resolved:
                        resolved.append(installed_pkg)
                    
                    # Recursively resolve dependencies of this package
                    resolve_recursive(installed_pkg, depth + 1)
                else:
                    # Dependency not installed
                    conflicts.append(DependencyConflict(
                        package=dep_name,
                        requested_version=version_constraint,
                        installed_version=None,
                        conflict_type="missing"
                    ))
        
        # Start resolution with the main package
        resolve_recursive(package)
        
        return resolved, conflicts
    
    def check_installation_compatibility(self, package: Package) -> List[DependencyConflict]:
        """Check if a package can be installed without conflicts."""
        conflicts = []
        
        # Check for version conflicts with installed packages
        for dep_name, version_constraint in package.metadata.dependencies.items():
            if dep_name in self.installed_packages:
                installed_pkg = self.installed_packages[dep_name]
                
                if not self._check_version_compatibility(
                    installed_pkg.version, version_constraint
                ):
                    conflicts.append(DependencyConflict(
                        package=dep_name,
                        requested_version=version_constraint,
                        installed_version=installed_pkg.version,
                        conflict_type="version_conflict"
                    ))
        
        return conflicts
    
    def get_installation_order(self, packages: List[Package]) -> List[Package]:
        """Get the correct installation order for packages based on dependencies."""
        # Simple topological sort
        visited = set()
        result = []
        
        def visit(pkg: Package) -> None:
            if pkg.name in visited:
                return
            
            visited.add(pkg.name)
            
            # Visit dependencies first
            for dep_name in pkg.metadata.dependencies:
                if dep_name in self.installed_packages:
                    dep_pkg = self.installed_packages[dep_name]
                    visit(dep_pkg)
            
            result.append(pkg)
        
        for package in packages:
            visit(package)
        
        return result
    
    def _check_version_compatibility(self, installed_version: str, required_version: str) -> bool:
        """Check if an installed version satisfies a required version constraint."""
        # Simple implementation for now
        # Could be extended to support semantic versioning constraints
        
        if required_version == "*" or required_version == "latest":
            return True
        
        # Exact version match
        if installed_version == required_version:
            return True
        
        # Simple range matching (e.g., ">=1.0.0", "<2.0.0")
        try:
            if required_version.startswith(">="):
                min_version = required_version[2:]
                return self._compare_versions(installed_version, min_version) >= 0
            elif required_version.startswith("<="):
                max_version = required_version[2:]
                return self._compare_versions(installed_version, max_version) <= 0
            elif required_version.startswith(">"):
                min_version = required_version[1:]
                return self._compare_versions(installed_version, min_version) > 0
            elif required_version.startswith("<"):
                max_version = required_version[1:]
                return self._compare_versions(installed_version, max_version) < 0
        except Exception:
            pass
        
        return False
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings."""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Pad with zeros to make same length
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 < v2:
                    return -1
                elif v1 > v2:
                    return 1
            
            return 0
        except Exception:
            # Fallback to string comparison
            if version1 < version2:
                return -1
            elif version1 > version2:
                return 1
            else:
                return 0
