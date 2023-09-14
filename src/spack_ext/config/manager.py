"""Configuration manager implementation."""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from spack_ext.config.models import CompilerConfig, PackageConfig, SiteConfig


class ConfigManager:
    """Manages Spack configuration generation and validation."""

    def __init__(self, templates_dir: Optional[Path] = None) -> None:
        """Initialize the configuration manager.

        Args:
            templates_dir: Path to Jinja2 templates directory
        """
        if templates_dir is None:
            pkg_dir = Path(__file__).parent.parent.parent.parent
            templates_dir = pkg_dir / "templates" / "configs"

        self.templates_dir = templates_dir
        self.env: Optional[Environment] = None

        if templates_dir.exists():
            self.env = Environment(
                loader=FileSystemLoader(str(templates_dir)),
                autoescape=select_autoescape(),
                trim_blocks=True,
                lstrip_blocks=True,
            )

    def generate(
        self,
        auto_detect: bool = False,
        arch: Optional[str] = None,
        site: Optional[str] = None,
        provider: Optional[str] = None,
        instance_type: Optional[str] = None,
    ) -> SiteConfig:
        """Generate site configuration.

        Args:
            auto_detect: Auto-detect system characteristics
            arch: Target architecture
            site: Site name
            provider: Cloud/HPC provider
            instance_type: Cloud instance type

        Returns:
            Generated site configuration
        """
        detected_compilers: list[CompilerConfig] = []
        detected_arch = arch

        if auto_detect:
            detected_compilers = self._detect_compilers()
            detected_arch = self._detect_architecture()

        site_name = site or "default-site"
        target_arch = detected_arch or "x86_64"

        config = SiteConfig(
            site_name=site_name,
            architecture=target_arch,
            compilers=detected_compilers,
            packages={},
            provider=provider,
            metadata={
                "instance_type": instance_type,
                "auto_generated": auto_detect,
            },
        )

        # Add common package configurations
        config.packages["all"] = PackageConfig(
            name="all",
            variants=[],
            buildable=True,
        )

        # Add provider-specific configurations
        if provider == "aws":
            self._add_aws_configs(config, instance_type)
        elif provider == "gcp":
            self._add_gcp_configs(config, instance_type)

        return config

    def _detect_compilers(self) -> list[CompilerConfig]:
        """Detect available compilers on the system.

        Returns:
            List of detected compiler configurations
        """
        compilers: list[CompilerConfig] = []

        # Try to find GCC
        gcc_path = shutil.which("gcc")
        if gcc_path:
            try:
                result = subprocess.run(
                    [gcc_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    version_line = result.stdout.split("\n")[0]
                    # Extract version (simplified)
                    version = version_line.split()[-1]

                    compilers.append(
                        CompilerConfig(
                            name="gcc",
                            version=version,
                            cc=gcc_path,
                            cxx=shutil.which("g++") or "/usr/bin/g++",
                            f77=shutil.which("gfortran"),
                            f90=shutil.which("gfortran"),
                        )
                    )
            except (subprocess.TimeoutExpired, IndexError):
                pass

        # Try to find Clang
        clang_path = shutil.which("clang")
        if clang_path:
            try:
                result = subprocess.run(
                    [clang_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    version_line = result.stdout.split("\n")[0]
                    parts = version_line.split()
                    version = parts[2] if len(parts) > 2 else "unknown"

                    compilers.append(
                        CompilerConfig(
                            name="clang",
                            version=version,
                            cc=clang_path,
                            cxx=shutil.which("clang++") or "/usr/bin/clang++",
                        )
                    )
            except (subprocess.TimeoutExpired, IndexError):
                pass

        return compilers

    def _detect_architecture(self) -> str:
        """Detect system architecture.

        Returns:
            Architecture string
        """
        machine = platform.machine()
        if machine == "x86_64":
            # Try to detect microarchitecture level
            return "x86_64_v3"  # Conservative default
        elif machine.startswith("aarch64") or machine.startswith("arm"):
            return "aarch64"
        return machine

    def _add_aws_configs(
        self,
        config: SiteConfig,
        instance_type: Optional[str],
    ) -> None:
        """Add AWS-specific configurations.

        Args:
            config: Site configuration to modify
            instance_type: AWS instance type
        """
        # Detect CPU architecture from instance type
        if instance_type:
            if "graviton" in instance_type.lower() or instance_type.startswith("m6g"):
                config.architecture = "neoverse_n1"
            elif instance_type.startswith("c7i"):
                config.architecture = "icelake"
            elif instance_type.startswith("c7a"):
                config.architecture = "zen4"

        # Add AWS-specific package preferences
        config.packages["openmpi"] = PackageConfig(
            name="openmpi",
            variants=["+pmi"],
            buildable=True,
        )

    def _add_gcp_configs(
        self,
        config: SiteConfig,
        instance_type: Optional[str],
    ) -> None:
        """Add GCP-specific configurations.

        Args:
            config: Site configuration to modify
            instance_type: GCP instance type
        """
        # GCP-specific optimizations
        if instance_type and "t2a" in instance_type:
            config.architecture = "neoverse_n1"

    def write(self, config: SiteConfig, output_dir: str) -> None:
        """Write configuration to files.

        Args:
            config: Site configuration to write
            output_dir: Output directory path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write compilers.yaml
        compilers_data = {
            "compilers": [
                {
                    "compiler": {
                        "spec": f"{c.name}@{c.version}",
                        "paths": {
                            "cc": c.cc,
                            "cxx": c.cxx,
                            "f77": c.f77 or "/usr/bin/false",
                            "fc": c.f90 or "/usr/bin/false",
                        },
                        "flags": c.flags,
                        "operating_system": platform.system().lower(),
                        "target": config.architecture,
                        "modules": [],
                    }
                }
                for c in config.compilers
            ]
        }

        with open(output_path / "compilers.yaml", "w") as f:
            yaml.dump(compilers_data, f, default_flow_style=False, sort_keys=False)

        # Write packages.yaml
        packages_data = {
            "packages": {
