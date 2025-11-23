"""Pydantic models for provider configuration."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class DeprecatedModel(BaseModel):
    """Information about a deprecated or legacy model."""

    model_id: str = Field(..., description="Model identifier (e.g., 'text-davinci-003')")
    deprecation_date: Optional[date] = Field(None, description="Date when the model was deprecated")
    retirement_date: Optional[date] = Field(None, description="Date when the model will be/was retired")
    replacement: Optional[str] = Field(None, description="Suggested replacement model")
    notes: Optional[str] = Field(None, description="Additional notes about the deprecation")


class ProviderModelConfig(BaseModel):
    """Model configuration for a provider."""

    live: list[str] = Field(
        default_factory=list,
        description="List of currently supported/live model IDs",
    )
    legacy: list[DeprecatedModel] = Field(
        default_factory=list,
        description="List of legacy models (scheduled for future deprecation)",
    )
    deprecated: list[DeprecatedModel] = Field(
        default_factory=list,
        description="List of already deprecated models",
    )


class ProviderInfo(BaseModel):
    """Information about a single provider."""

    provider: str = Field(..., description="Provider name (e.g., 'OpenAI', 'Anthropic')")
    safety_level: str = Field(..., description="Safety level: 'safe', 'worrying', or 'dangerous'")
    models: ProviderModelConfig = Field(..., description="Model configuration for this provider")


class ProviderConfig(BaseModel):
    """Unified configuration for all providers."""

    providers: dict[str, ProviderInfo] = Field(
        ...,
        description="Provider configurations by provider name",
    )

    def get_safe_providers(self) -> list[str]:
        """Get list of safe provider names."""
        return [name for name, info in self.providers.items() if info.safety_level == "safe"]

    def get_worrying_providers(self) -> list[str]:
        """Get list of worrying provider names."""
        return [name for name, info in self.providers.items() if info.safety_level == "worrying"]

    def get_dangerous_providers(self) -> list[str]:
        """Get list of dangerous provider names."""
        return [name for name, info in self.providers.items() if info.safety_level == "dangerous"]

    def get_deprecated_models(self, provider: str) -> list[DeprecatedModel]:
        """Get deprecated models for a provider."""
        if provider in self.providers:
            return self.providers[provider].models.deprecated
        return []

    def get_legacy_models(self, provider: str) -> list[DeprecatedModel]:
        """Get legacy models for a provider."""
        if provider in self.providers:
            return self.providers[provider].models.legacy
        return []
