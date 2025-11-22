"""Logging configuration for neops CLI.

This module provides centralized logging configuration with support for
multiple verbosity levels following Unix conventions.
"""

import logging
import sys


def setup_logging(verbosity: int = 0) -> logging.Logger:
    """Configure logging based on verbosity level.

    Parameters
    ----------
    verbosity : int, optional
        Verbosity level (default: 0)
        - 0: WARNING level, minimal output
        - 1: INFO level, general information
        - 2: DEBUG level, detailed debugging with timestamps
        - 3+: DEBUG level including third-party libraries

    Returns
    -------
    logging.Logger
        Configured logger instance for the neops package

    Examples
    --------
    >>> logger = setup_logging(verbosity=1)
    >>> logger.info("This will be shown")
    >>> logger.debug("This will not be shown")

    >>> logger = setup_logging(verbosity=2)
    >>> logger.debug("This will be shown with timestamps")
    """
    # Map verbosity count to log levels
    level_map = {
        0: logging.WARNING,
        1: logging.INFO,
    }
    level = level_map.get(verbosity, logging.DEBUG)

    # Configure format based on verbosity
    if verbosity >= 2:
        # Detailed format for debug mode with timestamps and location
        log_format = "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    else:
        # Simple format for info/warning
        log_format = "[%(levelname)s] %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stderr)],
        force=True,  # Override any existing configuration
    )

    # Get logger for neops package
    logger = logging.getLogger("neops")
    logger.setLevel(level)

    # For very verbose mode, also show debug logs from dependencies
    if verbosity >= 3:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        # Silence noisy third-party libraries at lower verbosity levels
        _silence_noisy_loggers()

    level_name = logging.getLevelName(level)
    logger.debug("Logging configured: verbosity=%s level=%s", verbosity, level_name)

    return logger


def _silence_noisy_loggers() -> None:
    """Silence commonly noisy third-party library loggers.

    This prevents third-party libraries from cluttering the output
    at lower verbosity levels.
    """
    noisy_loggers = [
        "urllib3",
        "requests",
        "botocore",
        "boto3",
        "paramiko",
    ]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str = "neops") -> logging.Logger:
    """Get a logger instance for the given name.

    Parameters
    ----------
    name : str, optional
        Logger name, defaults to "neops"

    Returns
    -------
    logging.Logger
        Logger instance

    Examples
    --------
    >>> logger = get_logger(__name__)
    >>> logger.info("Module-specific logging")
    """
    return logging.getLogger(name)
