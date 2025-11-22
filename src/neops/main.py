"""Main CLI entry point for neops.

This module defines the command-line interface structure and commands.
"""

import typer

from neops.logging_config import get_logger, setup_logging

# Get logger for this module
logger = get_logger(__name__)

# Create the main Typer app
app = typer.Typer()


@app.callback()
def main_callback(
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help=("Increase verbosity (-v for INFO, -vv for DEBUG, -vvv for all debug)"),
    ),
) -> None:
    """Network Operations CLI Tool.

    Use -v for verbose output, -vv for debug,
    -vvv for all debug including dependencies.
    """
    setup_logging(verbosity=verbose)


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


# Add more commands here as needed
# @app.command()
# def another_command():
#     logger.info("Another command executed")
#     pass


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
