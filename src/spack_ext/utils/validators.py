"""Validation utility functions."""

from pathlib import Path
from typing import Any

import yaml


def validate_yaml(file_path: str) -> tuple[bool, Any, list[str]]:
    """Validate YAML file syntax.

    Args:
        file_path: Path to YAML file

    Returns:
        Tuple of (is_valid, parsed_data, error_messages)
    """
    errors: list[str] = []

    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
        return True, data, []

    except yaml.YAMLError as e:
        errors.append(f"YAML syntax error: {e}")
        return False, None, errors

    except Exception as e:
        errors.append(f"Error reading file: {e}")
        return False, None, errors


def validate_path(path: str, must_exist: bool = False) -> tuple[bool, list[str]]:
    """Validate file/directory path.

    Args:
        path: Path to validate
        must_exist: Whether path must already exist

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors: list[str] = []

    try:
        p = Path(path)

        if must_exist and not p.exists():
            errors.append(f"Path does not exist: {path}")
            return False, errors

        # Check if parent directory exists for new paths
        if not must_exist and not p.parent.exists():
            errors.append(f"Parent directory does not exist: {p.parent}")
            return False, errors

        return True, []

    except Exception as e:
        errors.append(f"Invalid path: {e}")
        return False, errors
