"""Configuration management for neops.

This module handles pyproject.toml discovery, loading, and parsing.
"""

import tomllib
from pathlib import Path
from typing import Any, Optional

from neops.logging_config import get_logger

logger = get_logger(__name__)


class PyProjectNotFoundError(FileNotFoundError):
    """Raised when pyproject.toml cannot be found."""

    pass


class PyProjectParseError(ValueError):
    """Raised when pyproject.toml cannot be parsed."""

    pass


def find_repo_root(start_path: Optional[Path] = None) -> Path:
    """Find the repository root by looking for .git directory.

    Parameters
    ----------
    start_path : Path, optional
        Directory to start searching from (default: current directory)

    Returns
    -------
    Path
        Path to the repository root

    Raises
    ------
    PyProjectNotFoundError
        If no repository root can be found
    """
    if start_path is None:
        start_path = Path.cwd()

    logger.debug(f"Searching for repository root from: {start_path}")

    current = start_path.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            logger.debug(f"Found repository root at: {parent}")
            return parent

    # If no .git found, try finding pyproject.toml
    current = start_path.resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            logger.debug(f"Found pyproject.toml at: {parent}")
            return parent

    # Fall back to current directory
    logger.warning(f"No .git or pyproject.toml found in parent directories, using current directory: {start_path}")
    return start_path


def find_pyproject_toml(custom_path: Optional[Path] = None) -> Path:
    """Find and validate the pyproject.toml file path.

    Parameters
    ----------
    custom_path : Path, optional
        Custom path to pyproject.toml file or directory containing it

    Returns
    -------
    Path
        Absolute path to the pyproject.toml file

    Raises
    ------
    PyProjectNotFoundError
        If the file cannot be found
    """
    if custom_path is not None:
        custom_path = Path(custom_path).resolve()
        logger.debug(f"Using custom path: {custom_path}")

        # If it's a directory, look for pyproject.toml in it
        if custom_path.is_dir():
            pyproject_path = custom_path / "pyproject.toml"
        else:
            pyproject_path = custom_path

        if not pyproject_path.exists():
            raise PyProjectNotFoundError(f"pyproject.toml not found at: {pyproject_path}")

        logger.info(f"Found pyproject.toml at: {pyproject_path}")
        return pyproject_path

    # Default: search from repository root
    repo_root = find_repo_root()
    pyproject_path = repo_root / "pyproject.toml"

    if not pyproject_path.exists():
        raise PyProjectNotFoundError(f"pyproject.toml not found at repository root: {repo_root}")

    logger.info(f"Found pyproject.toml at: {pyproject_path}")
    return pyproject_path


def load_pyproject_toml(path: Path) -> dict[str, Any]:
    """Load and parse a pyproject.toml file.

    Parameters
    ----------
    path : Path
        Path to the pyproject.toml file

    Returns
    -------
    dict[str, Any]
        Parsed TOML data as a dictionary

    Raises
    ------
    PyProjectParseError
        If the file cannot be parsed
    """
    logger.debug(f"Loading pyproject.toml from: {path}")

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        logger.debug(f"Successfully parsed pyproject.toml ({len(data)} top-level keys)")
        return data
    except Exception as e:
        raise PyProjectParseError(f"Failed to parse {path}: {e}") from e


def get_project_config(custom_path: Optional[Path] = None) -> dict[str, Any]:
    """Get the project configuration from pyproject.toml.

    This is the main entry point for loading project configuration.

    Parameters
    ----------
    custom_path : Path, optional
        Custom path to pyproject.toml file or directory

    Returns
    -------
    dict[str, Any]
        Parsed pyproject.toml data

    Raises
    ------
    PyProjectNotFoundError
        If the file cannot be found
    PyProjectParseError
        If the file cannot be parsed

    Examples
    --------
    >>> config = get_project_config()
    >>> print(config['project']['name'])
    'neops'

    >>> config = get_project_config(Path('/custom/path/pyproject.toml'))
    """
    pyproject_path = find_pyproject_toml(custom_path)
    config = load_pyproject_toml(pyproject_path)

    # Log some useful information
    if "project" in config and "name" in config["project"]:
        logger.info(f"Loaded project: {config['project']['name']}")
        if "version" in config["project"]:
            logger.info(f"Project version: {config['project']['version']}")

    return config
