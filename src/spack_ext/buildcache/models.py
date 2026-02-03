"""Data models for buildcache management."""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class MirrorType(str, Enum):
    """Mirror storage types."""

    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    HTTPS = "https"
    OCI = "oci"


class Mirror(BaseModel):
    """Buildcache mirror configuration."""

    name: str = Field(..., description="Mirror name")
    url: str = Field(..., description="Mirror URL")
    mirror_type: MirrorType = Field(default=MirrorType.HTTPS, description="Storage type")
    fetch: bool = Field(default=True, description="Fetch from this mirror")
    push: bool = Field(default=False, description="Push to this mirror")
    signed: bool = Field(default=False, description="Verify signatures")
    trust_key: Optional[str] = Field(default=None, description="GPG key ID for verification")


class BuildcacheConfig(BaseModel):
    """Buildcache configuration."""

    mirrors: list[Mirror] = Field(default_factory=list, description="Configured mirrors")
    default_mirror: Optional[str] = Field(default=None, description="Default mirror for push")
    compression: str = Field(default="zstd", description="Compression algorithm")
    verify_checksums: bool = Field(default=True, description="Verify package checksums")
    gpg_signing: bool = Field(default=False, description="Enable GPG signing")
    gpg_key: Optional[str] = Field(default=None, description="GPG key for signing")
    rebuild_index: bool = Field(default=True, description="Rebuild index after push")


class BuildcacheStats(BaseModel):
    """Buildcache statistics."""

    mirror_name: str
    total_packages: int = 0
    total_size_mb: float = 0.0
    compilers: set[str] = Field(default_factory=set)
    architectures: set[str] = Field(default_factory=set)
    last_updated: Optional[str] = None
