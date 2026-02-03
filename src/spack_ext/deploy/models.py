"""Deployment data models."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class Stage(BaseModel):
    """Deployment stage definition."""

    name: str = Field(..., description="Stage name")
    environment: str = Field(..., description="Path to Spack environment file")
    depends: list[str] = Field(
        default_factory=list,
        description="Dependencies on other stages",
    )
    parallel: int = Field(1, description="Parallel job count")
    artifacts: list[str] = Field(
        default_factory=list,
        description="Artifacts to preserve",
    )


class DeploymentConfig(BaseModel):
    """Deployment configuration model."""

    name: str = Field(..., description="Deployment name")
    base_path: str = Field(..., description="Base installation path")
    stages: list[Stage] = Field(..., description="Deployment stages")
    artifacts: dict[str, Any] = Field(
        default_factory=dict,
        description="Artifact configuration",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"
