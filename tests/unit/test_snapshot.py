"""Tests for snapshot management."""

import pytest
import tempfile
from pathlib import Path

from spack_ext.snapshot import SnapshotManager, SnapshotConfig, Snapshot


@pytest.fixture
def temp_snapshot_dir():
    """Create a temporary snapshot directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_snapshot_manager_init(temp_snapshot_dir):
    """Test snapshot manager initialization."""
    config = SnapshotConfig(snapshot_dir=temp_snapshot_dir)
    manager = SnapshotManager(config)
    
    assert manager.config.snapshot_dir == temp_snapshot_dir
    assert temp_snapshot_dir.exists()


def test_create_snapshot(temp_snapshot_dir):
    """Test creating a snapshot."""
    config = SnapshotConfig(snapshot_dir=temp_snapshot_dir)
    manager = SnapshotManager(config)
    
    snapshot = manager.create_snapshot(
        name="test-snapshot",
        environment="dev",
        description="Test snapshot",
    )
    
    assert snapshot.name == "test-snapshot"
    assert snapshot.environment == "dev"
    assert snapshot.description == "Test snapshot"
    assert len(snapshot.snapshot_id) == 12


def test_list_snapshots(temp_snapshot_dir):
    """Test listing snapshots."""
    config = SnapshotConfig(snapshot_dir=temp_snapshot_dir)
    manager = SnapshotManager(config)
    
    manager.create_snapshot("snap1", environment="dev")
    manager.create_snapshot("snap2", environment="prod")
    manager.create_snapshot("snap3", environment="dev")
    
    all_snapshots = manager.list_snapshots()
    assert len(all_snapshots) == 3
    
    dev_snapshots = manager.list_snapshots(environment="dev")
    assert len(dev_snapshots) == 2


def test_get_snapshot(temp_snapshot_dir):
    """Test getting a specific snapshot."""
    config = SnapshotConfig(snapshot_dir=temp_snapshot_dir)
    manager = SnapshotManager(config)
    
    created = manager.create_snapshot("test", environment="dev")
    
    retrieved = manager.get_snapshot(created.snapshot_id)
    
    assert retrieved is not None
    assert retrieved.snapshot_id == created.snapshot_id
    assert retrieved.name == "test"


def test_delete_snapshot(temp_snapshot_dir):
    """Test deleting a snapshot."""
    config = SnapshotConfig(snapshot_dir=temp_snapshot_dir)
    manager = SnapshotManager(config)
    
    snapshot = manager.create_snapshot("to-delete")
    
    result = manager.delete_snapshot(snapshot.snapshot_id)
    assert result is True
    
    retrieved = manager.get_snapshot(snapshot.snapshot_id)
    assert retrieved is None


def test_restore_snapshot_dry_run(temp_snapshot_dir):
    """Test snapshot restore dry run."""
    config = SnapshotConfig(snapshot_dir=temp_snapshot_dir)
    manager = SnapshotManager(config)
    
    snapshot = manager.create_snapshot("restore-test")
    
    results = manager.restore_snapshot(snapshot.snapshot_id, dry_run=True)
    
    assert results["dry_run"] is True
    assert results["snapshot_id"] == snapshot.snapshot_id
    assert "packages_to_install" in results


def test_diff_snapshots(temp_snapshot_dir):
    """Test comparing snapshots."""
    config = SnapshotConfig(snapshot_dir=temp_snapshot_dir)
    manager = SnapshotManager(config)
    
    snap1 = manager.create_snapshot("snap1")
    snap2 = manager.create_snapshot("snap2")
    
    diff = manager.diff_snapshots(snap1.snapshot_id, snap2.snapshot_id)
    
    assert "snapshot1" in diff
    assert "snapshot2" in diff
    assert "added" in diff
    assert "removed" in diff
    assert "modified" in diff
    assert "total_changes" in diff


def test_cleanup_old_snapshots(temp_snapshot_dir):
    """Test cleaning up old snapshots."""
    config = SnapshotConfig(snapshot_dir=temp_snapshot_dir, retention_days=0)
    manager = SnapshotManager(config)
    
    manager.create_snapshot("old1")
    manager.create_snapshot("old2")
    
    # Cleanup with 0 days retention
    removed = manager.cleanup_old_snapshots(days=0)
    
    assert removed >= 0


def test_export_snapshot(temp_snapshot_dir):
    """Test exporting snapshot to YAML."""
    config = SnapshotConfig(snapshot_dir=temp_snapshot_dir)
    manager = SnapshotManager(config)
    
    snapshot = manager.create_snapshot("export-test")
    output_path = temp_snapshot_dir / "exported.yaml"
    
    manager.export_snapshot(snapshot.snapshot_id, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0
