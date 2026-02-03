"""Unit tests for package management."""

import pytest
from spack_ext.packages import PackageManager, PackageDefinition


def test_package_creation() -> None:
    """Test package definition creation."""
    manager = PackageManager()
    package = manager.create(
        name="test-pkg",
        version="1.0.0",
        family="testing",
        dependencies=["python", "numpy"],
    )

    assert package.name == "test-pkg"
    assert package.version == "1.0.0"
    assert package.family == "testing"
    assert len(package.dependencies) == 2
    assert "quick" in package.profiles
    assert "optimized" in package.profiles
    assert "debug" in package.profiles


def test_package_profiles() -> None:
    """Test build profiles."""
    manager = PackageManager()
    package = manager.create(name="prof-test", version="2.0.0")

    quick = package.profiles["quick"]
    assert "~optimization" in quick.variants

    optimized = package.profiles["optimized"]
    assert "+optimization" in optimized.variants
    assert "-O3" in optimized.cflags or ""

    debug = package.profiles["debug"]
    assert "+debug" in debug.variants
