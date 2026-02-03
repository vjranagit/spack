"""Tests for buildcache management."""

import pytest
from pathlib import Path

from spack_ext.buildcache import BuildcacheManager, BuildcacheConfig, Mirror, MirrorType


def test_buildcache_manager_init():
    """Test buildcache manager initialization."""
    manager = BuildcacheManager()
    assert manager.config is not None
    assert isinstance(manager.config, BuildcacheConfig)


def test_add_mirror():
    """Test adding a mirror."""
    manager = BuildcacheManager()
    mirror = manager.add_mirror(
        name="test-mirror",
        url="https://cache.example.com",
        mirror_type=MirrorType.HTTPS,
        push=True,
    )
    
    assert mirror.name == "test-mirror"
    assert mirror.url == "https://cache.example.com"
    assert mirror.push is True
    assert len(manager.config.mirrors) == 1


def test_remove_mirror():
    """Test removing a mirror."""
    manager = BuildcacheManager()
    manager.add_mirror("test1", "https://test1.com")
    manager.add_mirror("test2", "https://test2.com")
    
    assert len(manager.config.mirrors) == 2
    
    result = manager.remove_mirror("test1")
    assert result is True
    assert len(manager.config.mirrors) == 1
    
    result = manager.remove_mirror("nonexistent")
    assert result is False


def test_list_mirrors():
    """Test listing mirrors."""
    manager = BuildcacheManager()
    manager.add_mirror("mirror1", "https://m1.com")
    manager.add_mirror("mirror2", "https://m2.com")
    
    mirrors = manager.list_mirrors()
    assert len(mirrors) == 2
    assert mirrors[0].name == "mirror1"
    assert mirrors[1].name == "mirror2"


def test_sync_mirror_dry_run():
    """Test mirror sync dry run."""
    manager = BuildcacheManager()
    manager.add_mirror("test", "https://test.com", push=True)
    
    stats = manager.sync_mirror("test", packages=["gcc", "python"], dry_run=True)
    
    assert stats["synced"] == 2
    assert stats["failed"] == 0


def test_sync_mirror_not_configured_for_push():
    """Test sync to mirror not configured for push."""
    manager = BuildcacheManager()
    manager.add_mirror("test", "https://test.com", push=False)
    
    with pytest.raises(ValueError, match="not configured for push"):
        manager.sync_mirror("test")


def test_verify_mirror():
    """Test mirror verification."""
    manager = BuildcacheManager()
    manager.add_mirror("https-mirror", "https://cache.example.com", mirror_type=MirrorType.HTTPS)
    
    results = manager.verify_mirror("https-mirror")
    
    assert results["mirror"] == "https-mirror"
    assert "accessible" in results
    assert "checksum_valid" in results


def test_create_index():
    """Test buildcache index creation."""
    manager = BuildcacheManager()
    manager.add_mirror("test", "https://test.com")
    
    result = manager.create_index("test")
    assert result is True


def test_get_stats():
    """Test getting buildcache stats."""
    manager = BuildcacheManager()
    manager.add_mirror("test", "https://test.com")
    
    stats = manager.get_stats("test")
    
    assert stats.mirror_name == "test"
    assert stats.total_packages >= 0
    assert stats.total_size_mb >= 0
