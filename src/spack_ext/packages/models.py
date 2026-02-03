"""Package data models."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class BuildProfile(BaseModel):
    """Build profile for a package."""

    name: str = Field(..., description="Profile name (quick, optimized, debug)")
    variants: list[str] = Field(
        default_factory=list,
        description="Spack variants for this profile",
    )
    cflags: Optional[str] = Field(None, description="C compiler flags")
    cxxflags: Optional[str] = Field(None, description="C++ compiler flags")
    fflags: Optional[str] = Field(None, description="Fortran compiler flags")


class PackageDefinition(BaseModel):
    """Package definition model."""

    name: str = Field(..., description="Package name")
    version: str = Field(..., description="Package version")
    family: Optional[str] = Field(None, description="Package family")
    description: Optional[str] = Field(None, description="Package description")
    dependencies: list[str] = Field(
        default_factory=list,
        description="Package dependencies",
    )
    profiles: dict[str, BuildProfile] = Field(
        default_factory=dict,
        description="Build profiles",
    )
    compatibility: dict[str, str] = Field(
        default_factory=dict,
        description="Compatibility constraints",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"
