"""Unit tests for optimization engine."""

import pytest
from spack_ext.optimize import OptimizationEngine


def test_cpu_detection() -> None:
    """Test CPU information detection."""
    engine = OptimizationEngine()
    cpu_info = engine.detect_cpu()

    assert cpu_info.brand
    assert cpu_info.arch
    assert cpu_info.vendor


def test_recommendations() -> None:
    """Test optimization recommendations."""
    engine = OptimizationEngine()
    recommendations = engine.get_recommendations()

    assert "target" in recommendations
    assert "compiler_flags" in recommendations
    assert "variants" in recommendations


def test_package_specific_recommendations() -> None:
    """Test package-specific recommendations."""
    engine = OptimizationEngine()
    recommendations = engine.get_recommendations(package="hpl")

    assert "variants" in recommendations
    assert isinstance(recommendations["variants"], list)
