"""
Falcon Package Manager (fpm) - npm/pip style interface
Shorter commands that mirror npm and pip functionality.
"""

import argparse
import sys
from pathlib import Path

from .manager import PackageManager
from .package import PackageMetadata


class FPMCLI:
    """Falcon Package Manager CLI with npm/pip style commands."""
    
    def __init__(self):
        self.manager = PackageManager()
    
    def run(self, args: Optional[list[str]] = None) -> int:
        """Run the FPM CLI with given arguments."""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            # Map commands to methods
            if hasattr(parsed_args, 'func'):
                return parsed_args.func(parsed_args)
            else:
                parser.print_help()
                return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for fpm commands."""
        parser = argparse.ArgumentParser(
            prog="fpm",
            description="Falcon Package Manager - npm/pip style interface"
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Install command (install)
        install_parser = subparsers.add_parser("install", help="Install a package")
        install_parser.add_argument("package", help="Package name or source")
        install_parser.set_defaults(func=self._cmd_install)
        
        # Short 'i' alias for install
        i_parser = subparsers.add_parser("i", help="Install a package (alias for install)")
        i_parser.add_argument("package", help="Package name or source")
        i_parser.set_defaults(func=self._cmd_install)
        
        # Uninstall command (uninstall/un)
        uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a package")
        uninstall_parser.add_argument("package", help="Package name to uninstall")
        uninstall_parser.set_defaults(func=self._cmd_uninstall)
        
        # Short 'un' alias for uninstall
        un_parser = subparsers.add_parser("un", help="Uninstall a package (alias for uninstall)")
        un_parser.add_argument("package", help="Package name to uninstall")
        un_parser.set_defaults(func=self._cmd_uninstall)
        
        # List command (list)
        list_parser = subparsers.add_parser("list", help="List installed packages")
        list_parser.add_argument("--search", help="Filter packages by search term")
        list_parser.set_defaults(func=self._cmd_list)
        
        # Info command (info)
        info_parser = subparsers.add_parser("info", help="Show package information")
        info_parser.add_argument("package", help="Package name")
        info_parser.set_defaults(func=self._cmd_info)
        
        # Create command (create)
        create_parser = subparsers.add_parser("create", help="Create a new package")
        create_parser.add_argument("name", help="Package name")
        create_parser.add_argument("--description", default="", help="Package description")
        create_parser.add_argument("--author", help="Package author")
        create_parser.add_argument("--version", default="1.0.0", help="Package version")
        create_parser.add_argument("--directory", default=".", help="Directory to create package in")
        create_parser.set_defaults(func=self._cmd_create)
        
        # Update command
        update_parser = subparsers.add_parser("update", help="Update packages")
        update_parser.add_argument("package", nargs="?", help="Package to update (optional)")
        update_parser.set_defaults(func=self._cmd_update)
        
        # Search command
        search_parser = subparsers.add_parser("search", help="Search for packages")
        search_parser.add_argument("query", help="Search query")
        search_parser.set_defaults(func=self._cmd_search)
        
        return parser
    
    def _cmd_install(self, args) -> int:
        """Handle install command."""
        success, message = self.manager.install_package(args.package)
        
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
    
    def _cmd_update(self, args) -> int:
        """Handle update command."""
        if args.package:
            print(f"Updating package '{args.package}'...")
            # TODO: Implement package updates
            print("🔄 Update functionality coming soon!")
            return 0
        else:
            print("Updating all packages...")
            # TODO: Implement bulk updates
            print("🔄 Update functionality coming soon!")
            return 0
    
    def _cmd_search(self, args) -> int:
        """Handle search command."""
        print(f"Searching for '{args.query}'...")
        # TODO: Implement remote package search
        print("🔍 Remote package search coming soon!")
        print("For now, use 'fpm list --search <query>' to search installed packages.")
        return 0


def main() -> int:
    """Entry point for fpm CLI."""
    cli = FPMCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
