"""Default deprecation configuration loaded from YAML."""

from pathlib import Path
from typing import Optional

from neops.deprecations.models import DeprecationConfig

# Lazy-loaded default deprecation config
_default_deprecation_config: Optional[DeprecationConfig] = None


def _load_default_deprecation_config() -> DeprecationConfig:
    """Load default deprecation config from YAML."""
    from neops.config.loader import load_deprecation_config

    return load_deprecation_config()


def _get_default_deprecation_config() -> DeprecationConfig:
    """Get default deprecation config, loading if necessary."""
    global _default_deprecation_config
    if _default_deprecation_config is None:
        _default_deprecation_config = _load_default_deprecation_config()
    return _default_deprecation_config


# Module-level accessor that lazy-loads
def __getattr__(name: str):
    """Lazy-load DEFAULT_DEPRECATION_CONFIG on first access."""
    if name == "DEFAULT_DEPRECATION_CONFIG":
        return _get_default_deprecation_config()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_deprecation_config(project_root: Optional[Path] = None) -> DeprecationConfig:
    """Get deprecation configuration with pyproject.toml overrides applied.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        DeprecationConfig with overrides applied
    """
    from neops.config.loader import load_deprecation_config_with_overrides

    return load_deprecation_config_with_overrides(project_root)
