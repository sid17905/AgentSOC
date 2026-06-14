from datetime import UTC, datetime
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    abuseipdb_api_key: str = ""
    slack_webhook_url: str = ""
    github_token: str = ""
    github_repo: str = ""
    frontend_origin: str = "http://localhost:5173"
    auto_ingest_enabled: bool = False
    auto_ingest_dir: str = "samples/inbox"
    auto_ingest_archive_dir: str = "samples/processed"
    auto_ingest_error_dir: str = "samples/failed"
    auto_ingest_interval_seconds: float = 5.0
    auto_ingest_max_file_size_bytes: int = 10 * 1024 * 1024
    auto_fetch_enabled: bool = False
    auto_fetch_sources: str = ""
    auto_fetch_interval_seconds: float = 60.0
    auto_fetch_start_at_end: bool = False
    auto_fetch_max_bytes: int = 64 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


def utc_now() -> datetime:
    return datetime.now(UTC)
