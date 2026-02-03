"""Data models for health diagnostics."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health check status."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


class HealthCheck(BaseModel):
    """Individual health check result."""

    name: str = Field(..., description="Check name")
    status: HealthStatus = Field(..., description="Check status")
    message: str = Field(..., description="Status message")
    details: Optional[dict[str, any]] = Field(default=None, description="Additional details")
    fix_suggestion: Optional[str] = Field(default=None, description="How to fix if failed")


class HealthReport(BaseModel):
    """Complete health report."""

    checks: list[HealthCheck] = Field(default_factory=list)
    total_pass: int = 0
    total_warn: int = 0
    total_fail: int = 0
    total_skip: int = 0
    overall_status: HealthStatus = HealthStatus.PASS
    
    def add_check(self, check: HealthCheck) -> None:
        """Add a check and update counters."""
        self.checks.append(check)
        if check.status == HealthStatus.PASS:
            self.total_pass += 1
        elif check.status == HealthStatus.WARN:
            self.total_warn += 1
        elif check.status == HealthStatus.FAIL:
            self.total_fail += 1
        elif check.status == HealthStatus.SKIP:
            self.total_skip += 1
        
        # Update overall status
        if self.total_fail > 0:
            self.overall_status = HealthStatus.FAIL
        elif self.total_warn > 0 and self.overall_status != HealthStatus.FAIL:
            self.overall_status = HealthStatus.WARN
