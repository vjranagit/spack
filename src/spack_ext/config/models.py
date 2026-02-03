"""Configuration data models using Pydantic."""

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class CompilerConfig(BaseModel):
    """Compiler configuration model."""

    name: str = Field(..., description="Compiler name (e.g., gcc, clang)")
    version: str = Field(..., description="Compiler version")
    cc: str = Field(..., description="Path to C compiler")
    cxx: str = Field(..., description="Path to C++ compiler")
    f77: Optional[str] = Field(None, description="Path to Fortran 77 compiler")
    f90: Optional[str] = Field(None, description="Path to Fortran 90 compiler")
    flags: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Compiler flags by type (cflags, cxxflags, etc.)",
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate compiler version format."""
        if not v or not v[0].isdigit():
            raise ValueError("Version must start with a digit")
        return v


class PackageConfig(BaseModel):
    """Package configuration model."""

    name: str = Field(..., description="Package name")
    version: Optional[str] = Field(None, description="Preferred version")
    variants: list[str] = Field(default_factory=list, description="Package variants")
    externals: list[dict[str, Any]] = Field(
        default_factory=list,
        description="External package specs",
    )
    buildable: bool = Field(True, description="Whether package can be built")


class SiteConfig(BaseModel):
    """Complete site configuration model."""

    site_name: str = Field(..., description="Name of the HPC site")
    architecture: str = Field(..., description="Target architecture")
    compilers: list[CompilerConfig] = Field(
        default_factory=list,
        description="Available compilers",
    )
    packages: dict[str, PackageConfig] = Field(
        default_factory=dict,
        description="Package configurations",
    )
    modules: dict[str, Any] = Field(
        default_factory=dict,
        description="Module system configuration",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="General Spack configuration",
    )
    provider: Optional[str] = Field(None, description="Cloud/HPC provider")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"
        validate_assignment = True
