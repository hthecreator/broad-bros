"""File discovery and scanning utilities for neops.

This module handles finding files to scan, including git-tracked files
and custom file paths.
"""

import subprocess
from pathlib import Path
from typing import Optional

from neops.logging_config import get_logger

logger = get_logger(__name__)


class GitNotFoundError(RuntimeError):
    """Raised when git command is not available or not in a git repository."""

    pass


class FileNotFoundError(FileNotFoundError):
    """Raised when specified file(s) cannot be found."""

    pass


# Common code file extensions to scan
CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".c",
    ".cpp",
    ".cc",
    ".cxx",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".scala",
    ".sh",
    ".bash",
    ".zsh",
    ".sql",
    ".r",
    ".R",
    ".m",
    ".mm",
}


def is_code_file(path: Path) -> bool:
    """Check if a file is a code file based on extension.

    Parameters
    ----------
    path : Path
        Path to the file to check

    Returns
    -------
    bool
        True if the file has a code extension
    """
    return path.suffix.lower() in CODE_EXTENSIONS


def get_git_tracked_files(repo_root: Optional[Path] = None) -> list[Path]:
    """Get all files tracked by git in the repository.

    Parameters
    ----------
    repo_root : Path, optional
        Root of the git repository (default: current directory)

    Returns
    -------
    list[Path]
        List of paths to git-tracked files

    Raises
    ------
    GitNotFoundError
        If git is not available or not in a git repository
    """
    if repo_root is None:
        repo_root = Path.cwd()

    logger.debug(f"Getting git-tracked files from: {repo_root}")

    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )

        files = [repo_root / line.strip() for line in result.stdout.splitlines() if line.strip()]

        logger.info(f"Found {len(files)} git-tracked files")
        return files

    except subprocess.CalledProcessError as e:
        raise GitNotFoundError(f"Failed to get git-tracked files: {e.stderr.strip()}") from e
    except FileNotFoundError as e:
        raise GitNotFoundError("git command not found. Is git installed?") from e


def get_git_tracked_code_files(repo_root: Optional[Path] = None) -> list[Path]:
    """Get all code files tracked by git in the repository.

    Parameters
    ----------
    repo_root : Path, optional
        Root of the git repository (default: current directory)

    Returns
    -------
    list[Path]
        List of paths to git-tracked code files

    Raises
    ------
    GitNotFoundError
        If git is not available or not in a git repository
    """
    all_files = get_git_tracked_files(repo_root)
    code_files = [f for f in all_files if is_code_file(f)]

    logger.info(f"Filtered to {len(code_files)} code files (from {len(all_files)} total files)")

    return code_files


def resolve_file_paths(
    paths: Optional[list[Path]] = None,
    repo_root: Optional[Path] = None,
) -> list[Path]:
    """Resolve file paths to scan.

    If paths are provided, validates and returns them.
    If no paths provided, returns all git-tracked code files.

    Parameters
    ----------
    paths : list[Path], optional
        Explicit paths to files or directories to scan
    repo_root : Path, optional
        Root of the repository for git discovery

    Returns
    -------
    list[Path]
        List of resolved file paths to scan

    Raises
    ------
    FileNotFoundError
        If specified files don't exist
    GitNotFoundError
        If no paths provided and git discovery fails
    """
    # If explicit paths provided, validate and use them
    if paths:
        logger.debug(f"Resolving {len(paths)} explicit path(s)")
        resolved = []

        for path in paths:
            path = path.resolve()

            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")

            if path.is_file():
                resolved.append(path)
                logger.debug(f"Added file: {path}")
            elif path.is_dir():
                # Recursively find all code files in directory
                dir_files = [f for f in path.rglob("*") if f.is_file() and is_code_file(f)]
                resolved.extend(dir_files)
                logger.debug(f"Added {len(dir_files)} code files from directory: {path}")
            else:
                logger.warning(f"Skipping non-file, non-directory: {path}")

        logger.info(f"Resolved to {len(resolved)} file(s) to scan")
        return resolved

    # No explicit paths - use git-tracked code files
    logger.debug("No explicit paths provided, discovering git-tracked code files")

    if repo_root is None:
        repo_root = Path.cwd()

    return get_git_tracked_code_files(repo_root)


def validate_files_exist(files: list[Path]) -> None:
    """Validate that all files in the list exist.

    Parameters
    ----------
    files : list[Path]
        List of file paths to validate

    Raises
    ------
    FileNotFoundError
        If any file doesn't exist
    """
    missing = [f for f in files if not f.exists()]

    if missing:
        raise FileNotFoundError(f"File(s) not found: {', '.join(str(f) for f in missing)}")

    logger.debug(f"Validated {len(files)} file(s) exist")


def filter_code_files(files: list[Path]) -> list[Path]:
    """Filter a list of files to only include code files.

    Parameters
    ----------
    files : list[Path]
        List of file paths

    Returns
    -------
    list[Path]
        Filtered list containing only code files
    """
    code_files = [f for f in files if is_code_file(f)]

    if len(code_files) < len(files):
        logger.info(f"Filtered {len(files)} files to {len(code_files)} code files")

    return code_files
