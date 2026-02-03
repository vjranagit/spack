"""Data models for snapshot management."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class PackageInfo(BaseModel):
    """Information about an installed package."""

    name: str
    version: str
    hash: str
    spec: str
    compiler: Optional[str] = None
    dependencies: list[str] = Field(default_factory=list)


class Snapshot(BaseModel):
    """Environment snapshot."""

    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    name: str = Field(..., description="Snapshot name")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    environment: Optional[str] = Field(default=None, description="Spack environment name")
    packages: list[PackageInfo] = Field(default_factory=list)
    config_files: dict[str, str] = Field(default_factory=dict, description="Config file contents")
    metadata: dict[str, any] = Field(default_factory=dict)
    description: Optional[str] = None


class SnapshotConfig(BaseModel):
    """Snapshot configuration."""

    snapshot_dir: Path = Field(default=Path("~/.spack-ext/snapshots").expanduser())
    auto_snapshot: bool = Field(default=False, description="Auto-create snapshots before operations")
    retention_days: int = Field(default=30, description="Days to keep snapshots")
    compress: bool = Field(default=True, description="Compress snapshots")
    include_buildcache: bool = Field(default=False, description="Include buildcache references")
