"""Optimization data models."""

from pydantic import BaseModel, Field


class CPUInfo(BaseModel):
    """CPU information model."""

    brand: str = Field(..., description="CPU brand name")
    arch: str = Field(..., description="CPU architecture")
    features: list[str] = Field(default_factory=list, description="CPU features/extensions")
    vendor: str = Field(..., description="CPU vendor")
    family: str = Field("", description="CPU family")

    class Config:
        """Pydantic configuration."""

        extra = "allow"
