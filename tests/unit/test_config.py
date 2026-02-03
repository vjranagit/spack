"""Unit tests for configuration management."""

import pytest
from spack_ext.config import ConfigManager, SiteConfig


def test_config_generation() -> None:
    """Test basic configuration generation."""
    manager = ConfigManager()
    config = manager.generate(site="test-site", arch="x86_64")

    assert config.site_name == "test-site"
    assert config.architecture == "x86_64"
    assert isinstance(config, SiteConfig)


def test_auto_detect() -> None:
    """Test auto-detection of system configuration."""
    manager = ConfigManager()
    config = manager.generate(auto_detect=True)

    assert config.site_name
    assert config.architecture
    # Compilers may or may not be detected depending on system
    assert isinstance(config.compilers, list)


def test_aws_provider() -> None:
    """Test AWS provider configuration."""
    manager = ConfigManager()
    config = manager.generate(
        provider="aws",
        instance_type="c7i.24xlarge",
        site="aws-test",
    )

    assert config.provider == "aws"
    assert config.metadata.get("instance_type") == "c7i.24xlarge"
    # Should detect icelake architecture
    assert "icelake" in config.architecture or config.architecture == "icelake"
