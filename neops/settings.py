"""Settings for Neops using Pydantic BaseSettings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NeopsSettings(BaseSettings):
    """Settings for Neops configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields like agent_model from env
    )

    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for the AI agent",
        validation_alias="OPENAI_API_KEY",
    )

    @property
    def agent_model(self) -> str:
        """Agent model to use (hardcoded to gpt-4o, not overridable by env vars).

        Returns:
            The agent model string, always "openai:gpt-4o"
        """
        return "openai:gpt-4o"


# Global settings instance - will be initialized when imported
settings = NeopsSettings()
