"""Pydantic models for provider configuration."""

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """Configuration for model providers."""

    dangerous: list[str] = Field(
        default_factory=list,
        description="List of provider names considered dangerous",
    )
    safe: list[str] = Field(
        default_factory=list,
        description="List of provider names considered safe",
    )
    worrying: list[str] = Field(
        default_factory=list,
        description="List of provider names considered worrying",
    )
