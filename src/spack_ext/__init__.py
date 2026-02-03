"""Spack HPC Extension Framework.

A modern Python-based extension framework for Spack that simplifies HPC package
management through automated configuration generation, deployment orchestration,
and intelligent optimization.
"""

__version__ = "0.1.0"
__author__ = "vjranagit"
__license__ = "MIT OR Apache-2.0"

from spack_ext.config import ConfigManager
from spack_ext.packages import PackageManager
from spack_ext.deploy import DeploymentOrchestrator
from spack_ext.optimize import OptimizationEngine

__all__ = [
    "ConfigManager",
    "PackageManager",
    "DeploymentOrchestrator",
    "OptimizationEngine",
    "__version__",
]
