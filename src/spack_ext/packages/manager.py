"""Package manager implementation."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from spack_ext.packages.models import BuildProfile, PackageDefinition


class PackageManager:
    """Manages package definitions and operations."""

    def __init__(self, packages_dir: Optional[Path] = None) -> None:
        """Initialize package manager.

        Args:
            packages_dir: Directory containing package definitions
        """
        self.packages_dir = packages_dir or Path.cwd() / "packages"

    def create(
        self,
        name: str,
        version: str,
        family: Optional[str] = None,
        dependencies: Optional[list[str]] = None,
    ) -> PackageDefinition:
        """Create a new package definition.

        Args:
            name: Package name
            version: Package version
            family: Package family
            dependencies: List of dependencies

        Returns:
            Created package definition
        """
        # Create default profiles
        profiles = {
            "quick": BuildProfile(
                name="quick",
                variants=["~optimization"],
                cflags="-O1",
            ),
            "optimized": BuildProfile(
                name="optimized",
                variants=["+optimization"],
                cflags="-O3 -march=native",
            ),
            "debug": BuildProfile(
                name="debug",
                variants=["+debug", "~optimization"],
                cflags="-g -O0",
            ),
        }

        package = PackageDefinition(
            name=name,
            version=version,
            family=family,
            dependencies=dependencies or [],
            profiles=profiles,
        )

        return package

    def validate_file(self, package_file: str) -> tuple[bool, list[str]]:
        """Validate a package definition file.

        Args:
            package_file: Path to package YAML file

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors: list[str] = []

        try:
            with open(package_file) as f:
                data = yaml.safe_load(f)

            # Validate with Pydantic
            PackageDefinition(**data)

            return True, []

        except ValidationError as e:
            for error in e.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                errors.append(f"{field}: {error['msg']}")
            return False, errors

        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error: {e}")
            return False, errors

        except Exception as e:
            errors.append(f"Unexpected error: {e}")
            return False, errors

    def load(self, package_file: str) -> PackageDefinition:
        """Load package definition from file.

        Args:
            package_file: Path to package YAML file

        Returns:
            Loaded package definition
        """
        with open(package_file) as f:
            data = yaml.safe_load(f)

        return PackageDefinition(**data)

    def save(self, package: PackageDefinition, output_file: str) -> None:
        """Save package definition to file.

        Args:
            package: Package definition to save
            output_file: Output file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(
                package.model_dump(exclude_none=True),
                f,
                default_flow_style=False,
                sort_keys=False,
            )
