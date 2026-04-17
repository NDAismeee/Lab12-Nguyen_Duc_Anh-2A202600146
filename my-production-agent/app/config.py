from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"
    log_level: str = "INFO"

    agent_api_keys: str = Field(
        default="change-me",
        validation_alias=AliasChoices("AGENT_API_KEYS", "AGENT_API_KEY"),
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    redis_url: str = "redis://localhost:6379/0"

    rate_limit_per_minute: int = 10
    monthly_budget_usd: float = 10.0

    history_max_messages: int = 20


settings = Settings()

