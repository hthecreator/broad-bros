"""Default provider configuration loaded from YAML."""

from pathlib import Path
from typing import Optional

from neops.providers.models import ProviderConfig

# Lazy-loaded default provider config
_default_provider_config: Optional[ProviderConfig] = None


def _load_default_provider_config() -> ProviderConfig:
    """Load default provider config from YAML."""
    from neops.config.loader import load_provider_config

    return load_provider_config()


def _get_default_provider_config() -> ProviderConfig:
    """Get default provider config, loading if necessary."""
    global _default_provider_config
    if _default_provider_config is None:
        _default_provider_config = _load_default_provider_config()
    return _default_provider_config


# Module-level accessor that lazy-loads
def __getattr__(name: str):
    """Lazy-load DEFAULT_PROVIDER_CONFIG on first access."""
    if name == "DEFAULT_PROVIDER_CONFIG":
        return _get_default_provider_config()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_provider_config(project_root: Optional[Path] = None) -> ProviderConfig:
    """Get provider configuration with pyproject.toml overrides applied.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        ProviderConfig with overrides applied
    """
    from neops.config.loader import load_provider_config_with_overrides

    return load_provider_config_with_overrides(project_root)
