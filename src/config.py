"""
Configuration management for Android Action Kernel.
Loads settings from environment variables and explicit .env file.
"""

from __future__ import annotations

from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from constants import (
    DEVICE_DUMP_PATH as DEFAULT_DEVICE_DUMP_PATH,
    LOCAL_DUMP_PATH as DEFAULT_LOCAL_DUMP_PATH,
    DEFAULT_MAX_STEPS,
    DEFAULT_STEP_DELAY,
    DEFAULT_GROQ_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_BEDROCK_MODEL,
)

SUPPORTED_PROVIDERS = ("openai", "groq", "bedrock")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    adb_path: str = Field(default="adb", alias="ADB_PATH")
    max_steps: int = Field(default=DEFAULT_MAX_STEPS, alias="MAX_STEPS")
    step_delay: float = Field(default=DEFAULT_STEP_DELAY, alias="STEP_DELAY")

    llm_providers: List[str] = Field(default_factory=lambda: ["openai"], alias="LLM_PROVIDERS")

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default=DEFAULT_GROQ_MODEL, alias="GROQ_MODEL")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default=DEFAULT_OPENAI_MODEL, alias="OPENAI_MODEL")

    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    bedrock_model: str = Field(default=DEFAULT_BEDROCK_MODEL, alias="BEDROCK_MODEL")

    @field_validator("llm_providers", mode="before")
    @classmethod
    def parse_llm_providers(cls, value: object) -> List[str]:
        if value is None or value == "":
            return ["openai"]
        if isinstance(value, str):
            providers = [item.strip().lower() for item in value.split(",") if item.strip()]
            return providers or ["openai"]
        if isinstance(value, list):
            providers = [str(item).strip().lower() for item in value if str(item).strip()]
            return providers or ["openai"]
        return value  # type: ignore[return-value]


_settings = Settings()


class classproperty(property):
    def __get__(self, obj, owner):
        return self.fget(owner)


class Config:
    """Application configuration loaded from environment."""

    # ADB Configuration
    ADB_PATH: str = _settings.adb_path
    SCREEN_DUMP_PATH: str = DEFAULT_DEVICE_DUMP_PATH
    LOCAL_DUMP_PATH: str = DEFAULT_LOCAL_DUMP_PATH

    # Agent Configuration
    MAX_STEPS: int = _settings.max_steps
    STEP_DELAY: float = _settings.step_delay

    # Provider selection
    LLM_PROVIDERS: List[str] = _settings.llm_providers

    # Groq Configuration
    GROQ_API_KEY: str = _settings.groq_api_key
    GROQ_MODEL: str = _settings.groq_model

    # OpenAI Configuration
    OPENAI_API_KEY: str = _settings.openai_api_key
    OPENAI_MODEL: str = _settings.openai_model

    # AWS Bedrock Configuration
    AWS_REGION: str = _settings.aws_region
    BEDROCK_MODEL: str = _settings.bedrock_model

    @classmethod
    def _provider_has_credentials(cls, provider: str) -> bool:
        if provider == "groq":
            return bool(cls.GROQ_API_KEY)
        if provider == "openai":
            return bool(cls.OPENAI_API_KEY)
        if provider == "bedrock":
            return True
        return False

    @classmethod
    def resolve_provider(cls, require_credentials: bool = False) -> str:
        providers = cls.LLM_PROVIDERS or ["openai"]
        supported = [p for p in providers if p in SUPPORTED_PROVIDERS]
        if not supported:
            raise ValueError(
                "Unsupported LLM providers: "
                f"{', '.join(providers)}. Supported: {', '.join(SUPPORTED_PROVIDERS)}"
            )

        if require_credentials:
            for provider in supported:
                if cls._provider_has_credentials(provider):
                    return provider
            raise ValueError(
                "No valid LLM provider found. Provide credentials for one of: "
                f"{', '.join(supported)}"
            )

        for provider in supported:
            if cls._provider_has_credentials(provider):
                return provider
        return supported[0]

    @classproperty
    def LLM_PROVIDER(cls) -> str:
        return cls.resolve_provider()

    @classmethod
    def get_model(cls) -> str:
        """Get the model name based on the selected provider."""
        provider = cls.resolve_provider()
        if provider == "groq":
            return cls.GROQ_MODEL
        elif provider == "bedrock":
            return cls.BEDROCK_MODEL
        else:
            return cls.OPENAI_MODEL

    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present."""
        provider = cls.resolve_provider(require_credentials=True)
        if provider == "groq" and not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when using Groq provider")
        elif provider == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
        # Bedrock uses AWS credential chain, no explicit validation needed
