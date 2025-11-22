"""Pydantic models for deprecation configuration."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class DeprecatedModel(BaseModel):
    """Information about a deprecated model."""

    model_id: str = Field(..., description="Model identifier (e.g., 'text-davinci-003')")
    deprecation_date: Optional[date] = Field(None, description="Date when the model was deprecated")
    retirement_date: Optional[date] = Field(None, description="Date when the model will be/was retired")
    replacement: Optional[str] = Field(None, description="Suggested replacement model")
    notes: Optional[str] = Field(None, description="Additional notes about the deprecation")


class ProviderDeprecationConfig(BaseModel):
    """Deprecation configuration for a specific provider."""

    provider: str = Field(..., description="Provider name (e.g., 'OpenAI', 'Anthropic')")
    deprecated: list[DeprecatedModel] = Field(
        default_factory=list,
        description="List of already deprecated models",
    )
    legacy: list[DeprecatedModel] = Field(
        default_factory=list,
        description="List of legacy models (scheduled for future deprecation)",
    )


class DeprecationConfig(BaseModel):
    """Overall deprecation configuration for all providers."""

    providers: dict[str, ProviderDeprecationConfig] = Field(
        default_factory=dict,
        description="Deprecation configs by provider name",
    )
