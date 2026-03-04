"""
Package representation and metadata handling.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class PackageMetadata:
    """Metadata for a Falcon package."""
    
    # Required fields
    name: str
    version: str
    description: str
    
    # Optional fields
    author: Optional[str] = None
    license: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    
    # Dependencies
    dependencies: Dict[str, str] = None  # package_name -> version_constraint
    
    # Entry points
    main: Optional[str] = None  # Main module to import
    exports: List[str] = None  # Exported modules/functions
    
    # Package structure
    files: List[str] = None  # Files included in package
    
    def __post_init__(self):
        """Initialize default values."""
        if self.dependencies is None:
            self.dependencies = {}
        if self.exports is None:
            self.exports = []
        if self.files is None:
            self.files = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PackageMetadata":
        """Create from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "PackageMetadata":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def satisfies_dependency(self, package_name: str, version_constraint: str) -> bool:
        """Check if this package satisfies a dependency constraint."""
        if self.name != package_name:
            return False
        
        try:
            # Simple version matching for now
            # Could be extended to support semantic versioning constraints
            return self.version == version_constraint or version_constraint == "*"
        except Exception:
            return False


@dataclass
class Package:
    """A Falcon package with metadata and files."""
    
    metadata: PackageMetadata
    root_path: Path
    
    def __post_init__(self):
        """Initialize package after creation."""
        if not self.root_path.exists():
            raise ValueError(f"Package root path does not exist: {self.root_path}")
    
    @property
    def name(self) -> str:
        """Get package name."""
        return self.metadata.name
    
    @property
    def version(self) -> str:
        """Get package version."""
        return self.metadata.version
    
    @property
    def lib_path(self) -> Path:
        """Get library files path."""
        return self.root_path / "lib"
    
    @property
    def metadata_file(self) -> Path:
        """Get metadata file path."""
        return self.root_path / "falcon.pkg"
    
    def get_file_path(self, relative_path: str) -> Path:
        """Get full path to a package file."""
        return self.root_path / relative_path
    
    def get_lib_file(self, module_name: str) -> Path:
        """Get path to a library file."""
        return self.lib_path / f"{module_name}.fn"
    
    def read_file(self, relative_path: str) -> str:
        """Read a file from the package."""
        file_path = self.get_file_path(relative_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Package file not found: {relative_path}")
        
        return file_path.read_text(encoding="utf-8")
    
    def list_lib_files(self) -> List[Path]:
        """List all library files in the package."""
        if not self.lib_path.exists():
            return []
        
        return list(self.lib_path.glob("*.fn"))
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for the package."""
        hash_md5 = hashlib.md5()
        
        # Include metadata in checksum
        hash_md5.update(self.metadata.to_json().encode('utf-8'))
        
        # Include all files in checksum
        for file_path in self.root_path.rglob("*"):
            if file_path.is_file() and file_path.name != "falcon.pkg":
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    @classmethod
    def load_from_directory(cls, root_path: Path) -> "Package":
        """Load package from directory."""
        metadata_file = root_path / "falcon.pkg"
        
        if not metadata_file.exists():
            raise ValueError(f"Package metadata not found: {metadata_file}")
        
        metadata_json = metadata_file.read_text(encoding="utf-8")
        metadata = PackageMetadata.from_json(metadata_json)
        
        return cls(metadata=metadata, root_path=root_path)
    
    def save_metadata(self) -> None:
        """Save metadata to file."""
        self.metadata_file.write_text(self.metadata.to_json(), encoding="utf-8")
