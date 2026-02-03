"""Health checker implementation."""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from spack_ext.health.models import HealthCheck, HealthReport, HealthStatus


class HealthChecker:
    """Performs health checks on Spack installation."""

    def __init__(self, spack_root: Optional[Path] = None) -> None:
        """Initialize health checker."""
        self.spack_root = spack_root or Path(os.environ.get("SPACK_ROOT", "/opt/spack"))

    def run_all_checks(self) -> HealthReport:
        """Run all health checks."""
        report = HealthReport()
        
        report.add_check(self.check_spack_installation())
        report.add_check(self.check_compilers())
        report.add_check(self.check_disk_space())
        report.add_check(self.check_python_version())
        report.add_check(self.check_git_available())
        report.add_check(self.check_build_tools())
        report.add_check(self.check_module_system())
        report.add_check(self.check_config_files())
        
        return report

    def check_spack_installation(self) -> HealthCheck:
        """Check if Spack is properly installed."""
        if self.spack_root.exists() and (self.spack_root / "bin" / "spack").exists():
            return HealthCheck(
                name="Spack Installation",
                status=HealthStatus.PASS,
                message=f"Spack found at {self.spack_root}",
                details={"path": str(self.spack_root)},
            )
        else:
            return HealthCheck(
                name="Spack Installation",
                status=HealthStatus.FAIL,
                message="Spack installation not found",
                fix_suggestion=f"Set SPACK_ROOT or install Spack at {self.spack_root}",
            )

    def check_compilers(self) -> HealthCheck:
        """Check for available compilers."""
        compilers_found = []
        
        for compiler in ["gcc", "clang", "icc"]:
            if shutil.which(compiler):
                try:
                    result = subprocess.run(
                        [compiler, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        version = result.stdout.split("\n")[0]
                        compilers_found.append(f"{compiler}: {version}")
                except (subprocess.TimeoutExpired, IndexError):
                    pass
        
        if compilers_found:
            return HealthCheck(
                name="Compilers",
                status=HealthStatus.PASS,
                message=f"Found {len(compilers_found)} compiler(s)",
                details={"compilers": compilers_found},
            )
        else:
            return HealthCheck(
                name="Compilers",
                status=HealthStatus.FAIL,
                message="No compilers found",
                fix_suggestion="Install gcc, clang, or another compiler",
            )

    def check_disk_space(self) -> HealthCheck:
        """Check available disk space."""
        try:
            stat = shutil.disk_usage(self.spack_root)
            free_gb = stat.free / (1024**3)
            
            if free_gb > 50:
                status = HealthStatus.PASS
                message = f"{free_gb:.1f} GB free"
            elif free_gb > 10:
                status = HealthStatus.WARN
                message = f"Low disk space: {free_gb:.1f} GB free"
            else:
                status = HealthStatus.FAIL
                message = f"Critical disk space: {free_gb:.1f} GB free"
            
            return HealthCheck(
                name="Disk Space",
                status=status,
                message=message,
                details={"free_gb": round(free_gb, 1)},
                fix_suggestion="Free up disk space" if status != HealthStatus.PASS else None,
            )
        except Exception as e:
            return HealthCheck(
                name="Disk Space",
                status=HealthStatus.WARN,
                message=f"Could not check disk space: {e}",
            )

    def check_python_version(self) -> HealthCheck:
        """Check Python version."""
        version = platform.python_version()
        major, minor = map(int, version.split(".")[:2])
        
        if major == 3 and minor >= 11:
            return HealthCheck(
                name="Python Version",
                status=HealthStatus.PASS,
                message=f"Python {version}",
                details={"version": version},
            )
        elif major == 3 and minor >= 8:
            return HealthCheck(
                name="Python Version",
                status=HealthStatus.WARN,
                message=f"Python {version} (3.11+ recommended)",
                details={"version": version},
                fix_suggestion="Upgrade to Python 3.11 or newer",
            )
        else:
            return HealthCheck(
                name="Python Version",
                status=HealthStatus.FAIL,
                message=f"Python {version} is too old",
                details={"version": version},
                fix_suggestion="Upgrade to Python 3.11 or newer",
            )

    def check_git_available(self) -> HealthCheck:
        """Check if git is available."""
        git_path = shutil.which("git")
        
        if git_path:
            try:
                result = subprocess.run(
                    ["git", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                version = result.stdout.strip()
                return HealthCheck(
                    name="Git",
                    status=HealthStatus.PASS,
                    message=version,
                    details={"path": git_path},
                )
            except subprocess.TimeoutExpired:
                pass
        
        return HealthCheck(
            name="Git",
            status=HealthStatus.WARN,
            message="Git not found",
            fix_suggestion="Install git for fetching from repositories",
        )

    def check_build_tools(self) -> HealthCheck:
        """Check for essential build tools."""
        tools = {
            "make": False,
            "cmake": False,
            "patch": False,
            "tar": False,
        }
        
        for tool in tools:
            if shutil.which(tool):
                tools[tool] = True
        
        found_count = sum(tools.values())
        total_count = len(tools)
        
        if found_count == total_count:
            status = HealthStatus.PASS
            message = "All build tools available"
        elif found_count >= total_count // 2:
            status = HealthStatus.WARN
            message = f"{found_count}/{total_count} build tools found"
        else:
            status = HealthStatus.FAIL
            message = f"Only {found_count}/{total_count} build tools found"
        
        missing = [tool for tool, found in tools.items() if not found]
        
        return HealthCheck(
            name="Build Tools",
            status=status,
            message=message,
            details={"tools": tools, "missing": missing},
            fix_suggestion=f"Install missing tools: {', '.join(missing)}" if missing else None,
        )

    def check_module_system(self) -> HealthCheck:
        """Check for module system availability."""
        for module_cmd in ["module", "modulecmd"]:
            if shutil.which(module_cmd):
                return HealthCheck(
                    name="Module System",
                    status=HealthStatus.PASS,
                    message=f"Module system found: {module_cmd}",
                )
        
        return HealthCheck(
            name="Module System",
            status=HealthStatus.SKIP,
            message="No module system detected (optional)",
        )

    def check_config_files(self) -> HealthCheck:
        """Check Spack configuration files."""
        config_dir = Path.home() / ".spack"
        
        if not config_dir.exists():
            return HealthCheck(
                name="Config Files",
                status=HealthStatus.WARN,
                message="No Spack user config found",
                fix_suggestion="Run 'spack config edit' to create configs",
            )
        
        important_configs = ["compilers.yaml", "packages.yaml", "config.yaml"]
        found_configs = [
            cfg for cfg in important_configs
            if (config_dir / cfg).exists()
        ]
        
        if len(found_configs) >= 2:
            return HealthCheck(
                name="Config Files",
                status=HealthStatus.PASS,
                message=f"Found {len(found_configs)} config files",
                details={"configs": found_configs},
            )
        else:
            return HealthCheck(
                name="Config Files",
                status=HealthStatus.WARN,
                message=f"Only {len(found_configs)} config files found",
                details={"configs": found_configs},
                fix_suggestion="Configure Spack with 'spack config edit'",
            )
