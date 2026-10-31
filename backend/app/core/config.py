from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Match Copilot"
    app_env: str = "development"
    debug: bool = True
    port: int = 8000
    host: str = "0.0.0.0"

    database_url: str = "sqlite:///./match_copilot.db"

    # LLM Settings
    use_mock_llm: bool = True
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # Scoring rules
    scoring_rules_path: str = Field(
        default_factory=lambda: str(
            Path(__file__).resolve().parent.parent.parent / "scoring_rules.yaml"
        )
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
