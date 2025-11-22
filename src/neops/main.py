"""Main CLI entry point for neops.

This module defines the command-line interface structure and commands.
"""

from pathlib import Path
from typing import Optional

import typer

from neops.config import PyProjectNotFoundError, PyProjectParseError, get_project_config
from neops.logging_config import get_logger, setup_logging

# Get logger for this module
logger = get_logger(__name__)

# Create the main Typer app
app = typer.Typer()

# Global variable to store loaded configuration
_project_config: Optional[dict] = None


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
) -> None:
    """Network Operations CLI Tool.

    Use -v for verbose output, -vv for debug,
    -vvv for all debug including dependencies.
    """
    global _project_config

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


# Add more commands here as needed


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
