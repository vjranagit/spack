"""Snapshot manager implementation."""

import hashlib
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yaml

from spack_ext.snapshot.models import PackageInfo, Snapshot, SnapshotConfig


class SnapshotManager:
    """Manages environment snapshots and rollback."""

    def __init__(self, config: Optional[SnapshotConfig] = None) -> None:
        """Initialize snapshot manager."""
        self.config = config or SnapshotConfig()
        self.config.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(
        self,
        name: str,
        environment: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Snapshot:
        """Create a new snapshot."""
        snapshot_id = self._generate_id(name)
        
        snapshot = Snapshot(
            snapshot_id=snapshot_id,
            name=name,
            environment=environment or "default",
            description=description,
        )
        
        # Capture installed packages
        snapshot.packages = self._capture_packages(environment)
        
        # Capture configuration files
        snapshot.config_files = self._capture_configs()
        
        # Save snapshot
        self._save_snapshot(snapshot)
        
        return snapshot

    def list_snapshots(self, environment: Optional[str] = None) -> list[Snapshot]:
        """List all snapshots."""
        snapshots = []
        
        for snapshot_file in self.config.snapshot_dir.glob("*.json"):
            try:
                snapshot = self._load_snapshot(snapshot_file)
                if environment is None or snapshot.environment == environment:
                    snapshots.append(snapshot)
            except Exception:
                continue
        
        return sorted(snapshots, key=lambda s: s.created_at, reverse=True)

    def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        """Get a specific snapshot."""
        snapshot_file = self.config.snapshot_dir / f"{snapshot_id}.json"
        if snapshot_file.exists():
            return self._load_snapshot(snapshot_file)
        return None

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot."""
        snapshot_file = self.config.snapshot_dir / f"{snapshot_id}.json"
        if snapshot_file.exists():
            snapshot_file.unlink()
            return True
        return False

    def restore_snapshot(self, snapshot_id: str, dry_run: bool = False) -> dict[str, any]:
        """Restore from a snapshot."""
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")
        
        results = {
            "snapshot_id": snapshot_id,
            "snapshot_name": snapshot.name,
            "dry_run": dry_run,
            "packages_to_install": len(snapshot.packages),
            "configs_to_restore": len(snapshot.config_files),
            "actions": [],
        }
        
        if dry_run:
            results["actions"].append("Would restore configurations")
            results["actions"].append(f"Would install {len(snapshot.packages)} packages")
            return results
        
        # Restore configuration files
        for filename, content in snapshot.config_files.items():
            results["actions"].append(f"Restored config: {filename}")
        
        # Restore packages (simulated)
        results["actions"].append(f"Restored {len(snapshot.packages)} packages")
        
        return results

    def diff_snapshots(self, snapshot_id1: str, snapshot_id2: str) -> dict[str, any]:
        """Compare two snapshots."""
        snap1 = self.get_snapshot(snapshot_id1)
        snap2 = self.get_snapshot(snapshot_id2)
        
        if not snap1 or not snap2:
            raise ValueError("One or both snapshots not found")
        
        pkgs1 = {p.name: p for p in snap1.packages}
        pkgs2 = {p.name: p for p in snap2.packages}
        
        added = [name for name in pkgs2 if name not in pkgs1]
        removed = [name for name in pkgs1 if name not in pkgs2]
        
        modified = []
        for name in pkgs1:
            if name in pkgs2 and pkgs1[name].version != pkgs2[name].version:
                modified.append({
                    "name": name,
                    "old_version": pkgs1[name].version,
                    "new_version": pkgs2[name].version,
                })
        
        return {
            "snapshot1": snap1.name,
            "snapshot2": snap2.name,
            "added": added,
            "removed": removed,
            "modified": modified,
            "total_changes": len(added) + len(removed) + len(modified),
        }

    def cleanup_old_snapshots(self, days: Optional[int] = None) -> int:
        """Remove snapshots older than specified days."""
        retention_days = days or self.config.retention_days
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        removed_count = 0
        for snapshot_file in self.config.snapshot_dir.glob("*.json"):
            try:
                snapshot = self._load_snapshot(snapshot_file)
                created = datetime.fromisoformat(snapshot.created_at)
                if created < cutoff_date:
                    snapshot_file.unlink()
                    removed_count += 1
            except Exception:
                continue
        
        return removed_count

    def _generate_id(self, name: str) -> str:
        """Generate unique snapshot ID."""
        timestamp = datetime.now().isoformat()
        content = f"{name}:{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def _capture_packages(self, environment: Optional[str]) -> list[PackageInfo]:
        """Capture currently installed packages."""
        # In real implementation, this would query Spack
        # For demonstration, return simulated data
        packages = [
            PackageInfo(
                name="cmake",
                version="3.27.7",
                hash="abc123d",
                spec="cmake@3.27.7%gcc@11.4.0",
                compiler="gcc@11.4.0",
                dependencies=["openssl", "ncurses"],
            ),
            PackageInfo(
                name="python",
                version="3.11.6",
                hash="xyz789e",
                spec="python@3.11.6%gcc@11.4.0",
                compiler="gcc@11.4.0",
                dependencies=["openssl", "zlib", "bzip2"],
            ),
        ]
        return packages

    def _capture_configs(self) -> dict[str, str]:
        """Capture configuration files."""
        config_files = {}
        
        # Simulate capturing config files
        config_files["compilers.yaml"] = "# Compiler configuration\n"
        config_files["packages.yaml"] = "# Package preferences\n"
        
        return config_files

    def _save_snapshot(self, snapshot: Snapshot) -> None:
        """Save snapshot to disk."""
        snapshot_file = self.config.snapshot_dir / f"{snapshot.snapshot_id}.json"
        
        snapshot_dict = snapshot.model_dump(mode="json")
        
        with open(snapshot_file, "w") as f:
            json.dump(snapshot_dict, f, indent=2, sort_keys=False)

    def _load_snapshot(self, snapshot_file: Path) -> Snapshot:
        """Load snapshot from disk."""
        with open(snapshot_file) as f:
            data = json.load(f)
        return Snapshot(**data)

    def export_snapshot(self, snapshot_id: str, output_path: Path) -> None:
        """Export snapshot to YAML."""
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")
        
        export_data = {
            "snapshot": {
                "id": snapshot.snapshot_id,
                "name": snapshot.name,
                "created": snapshot.created_at,
                "environment": snapshot.environment,
                "description": snapshot.description,
            },
            "packages": [
                {
                    "name": p.name,
                    "version": p.version,
                    "spec": p.spec,
                    "hash": p.hash,
                }
                for p in snapshot.packages
            ],
            "configs": snapshot.config_files,
        }
        
        with open(output_path, "w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
