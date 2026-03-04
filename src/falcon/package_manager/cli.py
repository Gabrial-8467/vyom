"""
Command-line interface for Falcon package manager.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .manager import PackageManager
from .package import PackageMetadata


class PackageManagerCLI:
    """CLI interface for package management."""
    
    def __init__(self):
        self.manager = PackageManager()
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments."""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            # Execute the appropriate command
            return getattr(self, f"_cmd_{parsed_args.command}")(parsed_args)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            prog="falcon-pkg",
            description="Falcon Package Manager"
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Install command
        install_parser = subparsers.add_parser("install", help="Install a package")
        install_parser.add_argument("source", help="Package source (directory, file, or URL)")
        
        # Uninstall command
        uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a package")
        uninstall_parser.add_argument("package", help="Package name to uninstall")
        
        # List command
        list_parser = subparsers.add_parser("list", help="List installed packages")
        list_parser.add_argument("--search", help="Filter packages by search term")
        
        # Info command
        info_parser = subparsers.add_parser("info", help="Show package information")
        info_parser.add_argument("package", help="Package name")
        
        # Create command
        create_parser = subparsers.add_parser("create", help="Create a new package")
        create_parser.add_argument("name", help="Package name")
        create_parser.add_argument("--description", default="", help="Package description")
        create_parser.add_argument("--author", help="Package author")
        create_parser.add_argument("--version", default="1.0.0", help="Package version")
        create_parser.add_argument("--directory", default=".", help="Directory to create package in")
        
        # Dependencies command
        deps_parser = subparsers.add_parser("deps", help="Show package dependencies")
        deps_parser.add_argument("package", help="Package name")
        
        return parser
    
    def _cmd_install(self, args) -> int:
        """Handle install command."""
        success, message = self.manager.install_package(args.source)
        
        if success:
            print(f"✅ {message}")
            return 0
        else:
            print(f"❌ {message}", file=sys.stderr)
            return 1
    
    def _cmd_uninstall(self, args) -> int:
        """Handle uninstall command."""
        success, message = self.manager.uninstall_package(args.package)
        
        if success:
            print(f"✅ {message}")
            return 0
        else:
            print(f"❌ {message}", file=sys.stderr)
            return 1
    
    def _cmd_list(self, args) -> int:
        """Handle list command."""
        packages = self.manager.list_packages()
        
        if not packages:
            print("No packages installed.")
            return 0
        
        if args.search:
            packages = self.manager.search_packages(args.search)
            if not packages:
                print(f"No packages found matching '{args.search}'.")
                return 0
        
        print("Installed packages:")
        print("-" * 60)
        
        for package in sorted(packages, key=lambda p: p.name):
            print(f"{package.name:<20} v{package.version:<10} {package.metadata.description}")
        
        return 0
    
    def _cmd_info(self, args) -> int:
        """Handle info command."""
        info = self.manager.get_package_info(args.package)
        
        if not info:
            print(f"Package '{args.package}' not found.", file=sys.stderr)
            return 1
        
        print(f"Package: {info['name']}")
        print(f"Version: {info['version']}")
        print(f"Description: {info['description']}")
        print(f"Author: {info['author']}")
        print(f"License: {info['license']}")
        if info['homepage']:
            print(f"Homepage: {info['homepage']}")
        if info['repository']:
            print(f"Repository: {info['repository']}")
        print(f"Dependencies: {info['dependencies']}")
        print(f"Exports: {info['exports']}")
        print(f"Main: {info['main']}")
        
        return 0
    
    def _cmd_create(self, args) -> int:
        """Handle create command."""
        metadata = PackageMetadata(
            name=args.name,
            version=args.version,
            description=args.description,
            author=getattr(args, 'author', None)
        )
        
        directory = Path(args.directory)
        success, message = self.manager.create_package(directory, metadata)
        
        if success:
            print(f"✅ {message}")
            print(f"📁 Created at: {directory / args.name}")
            print("📝 Edit the metadata in falcon.pkg and add your .fn files to the lib/ directory.")
            return 0
        else:
            print(f"❌ {message}", file=sys.stderr)
            return 1
    
    def _cmd_deps(self, args) -> int:
        """Handle dependencies command."""
        satisfied, conflicts = self.manager.check_dependencies(args.package)
        
        if not satisfied and not conflicts:
            print(f"Package '{args.package}' not found.", file=sys.stderr)
            return 1
        
        print(f"Dependencies for '{args.package}':")
        
        if satisfied:
            print("\n✅ Satisfied dependencies:")
            for dep in satisfied:
                print(f"  - {dep}")
        
        if conflicts:
            print("\n❌ Conflicts:")
            for conflict in conflicts:
                if conflict.conflict_type == "missing":
                    print(f"  - {conflict.package} (missing, requires {conflict.requested_version})")
                elif conflict.conflict_type == "version_conflict":
                    print(f"  - {conflict.package} (installed {conflict.installed_version}, requires {conflict.requested_version})")
                else:
                    print(f"  - {conflict.package} ({conflict.conflict_type})")
        
        return 0 if not conflicts else 1


def main() -> int:
    """Entry point for falcon-pkg CLI."""
    cli = PackageManagerCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
