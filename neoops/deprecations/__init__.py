"""Deprecation-related models and default configurations."""

from neoops.deprecations.default import DEFAULT_DEPRECATION_CONFIG, get_deprecation_config
from neoops.deprecations.models import (
    DeprecatedModel,
    DeprecationConfig,
    ProviderDeprecationConfig,
)

__all__ = [
    "DeprecatedModel",
    "ProviderDeprecationConfig",
    "DeprecationConfig",
    "DEFAULT_DEPRECATION_CONFIG",
    "get_deprecation_config",
]
