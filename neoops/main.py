"""Main CLI entry point for neops.

This module defines the command-line interface structure and commands.
"""

from pathlib import Path
from typing import Optional

import typer

from neops.config import PyProjectNotFoundError, PyProjectParseError, get_project_config
from neops.file_scanner import GitNotFoundError, resolve_file_paths
from neops.logging_config import get_logger, setup_logging

# Get logger for this module
logger = get_logger(__name__)

# Create the main Typer app
app = typer.Typer()

# Global variables to store loaded configuration and files to scan
_project_config: Optional[dict] = None
_files_to_scan: list[Path] = []


@app.callback()
def main_callback(
    verbose: int = typer.Option(  # noqa: B008
        0,
        "--verbose",
        "-v",
        count=True,
        help=("Increase verbosity (-v for INFO, -vv for DEBUG, -vvv for all debug)"),
    ),
    pyproject: Optional[Path] = typer.Option(  # noqa: B008
        None,
        "--pyproject",
        "-p",
        help=("Path to pyproject.toml file or directory (default: repo root)"),
        exists=False,  # We'll handle validation ourselves
    ),
    files: Optional[list[Path]] = typer.Option(  # noqa: B008
        None,
        "--file",
        "-f",
        help=("File(s) or directory to scan (default: all git-tracked code files). Can be specified multiple times."),
        exists=False,  # We'll handle validation ourselves
    ),
) -> None:
    """Network Operations CLI Tool.

    Use -v for verbose output, -vv for debug,
    -vvv for all debug including dependencies.
    """
    global _project_config, _files_to_scan

    # Setup logging first
    setup_logging(verbosity=verbose)

    # Load project configuration
    try:
        _project_config = get_project_config(custom_path=pyproject)
        logger.debug("Configuration loaded successfully from pyproject.toml")
    except PyProjectNotFoundError as e:
        logger.error("Configuration error: %s", e)
        raise typer.Exit(code=1) from None
    except PyProjectParseError as e:
        logger.error("Failed to parse pyproject.toml: %s", e)
        raise typer.Exit(code=1) from None

    # Resolve files to scan
    try:
        _files_to_scan = resolve_file_paths(paths=files)
        logger.info("Resolved %s file(s) to scan", len(_files_to_scan))
    except (FileNotFoundError, GitNotFoundError) as e:
        logger.error("File resolution error: %s", e)
        raise typer.Exit(code=1) from None


@app.command()
def hello(
    name: str = typer.Argument(..., help="Name of person to greet"),
) -> None:
    """Say hello to someone.

    This is a sample command demonstrating the CLI structure.
    """
    logger.debug("Starting hello command with name: %s", name)
    logger.info("Greeting %s", name)
    logger.info("Hello %s", name)
    logger.debug("Hello command completed successfully")


@app.command()
def show_config() -> None:
    """Display the loaded project configuration.

    Shows information from the pyproject.toml file that was loaded.
    """
    logger.debug("Displaying project configuration")

    if _project_config is None:
        logger.error("No configuration loaded")
        raise typer.Exit(code=1)

    # Display project metadata
    if "project" in _project_config:
        project = _project_config["project"]
        logger.info("Project Configuration:")
        logger.info("  Name: %s", project.get("name", "N/A"))
        logger.info("  Version: %s", project.get("version", "N/A"))
        logger.info("  Description: %s", project.get("description", "N/A"))

        if "dependencies" in project:
            logger.info("\nDependencies (%s):", len(project["dependencies"]))
            for dep in project["dependencies"]:
                logger.info("  - %s", dep)

        logger.info("Configuration displayed successfully")
    else:
        logger.warning("No [project] section found in pyproject.toml")
        logger.warning("No project configuration found in pyproject.toml")


@app.command()
def list_files() -> None:
    """List all files that will be scanned.

    Shows the files discovered either from git or from explicit paths.
    """
    logger.debug("Listing files to scan")

    if not _files_to_scan:
        logger.warning("No files to scan")
        raise typer.Exit(code=1)

    logger.info("Files to scan (%s):", len(_files_to_scan))
    for file in sorted(_files_to_scan):
        logger.info("  %s", file)

    logger.info("Listed %s file(s)", len(_files_to_scan))


@app.command()
def scan() -> None:
    """Scan the discovered or specified files.

    This is a placeholder command demonstrating file access.
    Business logic for actual scanning will be added later.
    """
    logger.debug("Starting scan operation")

    if not _files_to_scan:
        logger.error("No files to scan")
        raise typer.Exit(code=1)

    logger.info("Scanning %s file(s)...", len(_files_to_scan))

    # Placeholder: demonstrate we can access the files
    for i, file in enumerate(_files_to_scan, 1):
        logger.debug("Processing file %s/%s: %s", i, len(_files_to_scan), file)
        # Business logic will go here
        if file.exists():
            logger.debug("File exists and is readable: %s", file)
        else:
            logger.warning("File not found: %s", file)

    logger.info("✓ Scan complete: %s files processed", len(_files_to_scan))
    logger.info("Scan completed successfully")


# Add more commands here as needed


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
