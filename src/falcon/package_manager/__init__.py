"""
Falcon Package Manager

Provides package installation, dependency resolution, and import system
for Falcon programming language.
"""

from .manager import PackageManager
from .package import Package, PackageMetadata
from .resolver import DependencyResolver
from .installer import PackageInstaller
from .config import PackageManagerConfig
from .fpm_cli import FPMCLI

__all__ = [
    "PackageManager",
    "Package", 
    "PackageMetadata",
    "DependencyResolver",
    "PackageInstaller",
    "PackageManagerConfig",
    "FPMCLI"
]
