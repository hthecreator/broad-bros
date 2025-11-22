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
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help=("Increase verbosity (-v for INFO, -vv for DEBUG, -vvv for all debug)"),
    ),
    pyproject: Optional[Path] = typer.Option(
        None,
        "--pyproject",
        "-p",
        help=("Path to pyproject.toml file or directory (default: repo root)"),
        exists=False,  # We'll handle validation ourselves
    ),
    files: Optional[list[Path]] = typer.Option(
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
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(code=1)
    except PyProjectParseError as e:
        logger.error(f"Failed to parse pyproject.toml: {e}")
        raise typer.Exit(code=1)

    # Resolve files to scan
    try:
        _files_to_scan = resolve_file_paths(paths=files)
        logger.info(f"Resolved {len(_files_to_scan)} file(s) to scan")
    except (FileNotFoundError, GitNotFoundError) as e:
        logger.error(f"File resolution error: {e}")
        raise typer.Exit(code=1)


@app.command()
def hello(
    name: str = typer.Argument(..., help="Name of person to greet"),
) -> None:
    """Say hello to someone.

    This is a sample command demonstrating the CLI structure.
    """
    logger.debug(f"Starting hello command with name: {name}")
    logger.info(f"Greeting {name}")

    # Use print for actual output (not logging)
    print(f"Hello {name}")

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
        print("Project Configuration:")
        print(f"  Name: {project.get('name', 'N/A')}")
        print(f"  Version: {project.get('version', 'N/A')}")
        print(f"  Description: {project.get('description', 'N/A')}")

        if "dependencies" in project:
            print(f"\nDependencies ({len(project['dependencies'])}):")
            for dep in project["dependencies"]:
                print(f"  - {dep}")

        logger.info("Configuration displayed successfully")
    else:
        logger.warning("No [project] section found in pyproject.toml")
        print("No project configuration found in pyproject.toml")


@app.command()
def list_files() -> None:
    """List all files that will be scanned.

    Shows the files discovered either from git or from explicit paths.
    """
    logger.debug("Listing files to scan")

    if not _files_to_scan:
        logger.warning("No files to scan")
        print("No files to scan")
        raise typer.Exit(code=1)

    print(f"Files to scan ({len(_files_to_scan)}):")
    for file in sorted(_files_to_scan):
        print(f"  {file}")

    logger.info(f"Listed {len(_files_to_scan)} file(s)")


@app.command()
def scan() -> None:
    """Scan the discovered or specified files.

    This is a placeholder command demonstrating file access.
    Business logic for actual scanning will be added later.
    """
    logger.debug("Starting scan operation")

    if not _files_to_scan:
        logger.error("No files to scan")
        print("No files to scan")
        raise typer.Exit(code=1)

    print(f"Scanning {len(_files_to_scan)} file(s)...")

    # Placeholder: demonstrate we can access the files
    for i, file in enumerate(_files_to_scan, 1):
        logger.debug(f"Processing file {i}/{len(_files_to_scan)}: {file}")
        # Business logic will go here
        if file.exists():
            logger.debug(f"File exists and is readable: {file}")
        else:
            logger.warning(f"File not found: {file}")

    print(f"✓ Scan complete: {len(_files_to_scan)} files processed")
    logger.info("Scan completed successfully")


# Add more commands here as needed


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
