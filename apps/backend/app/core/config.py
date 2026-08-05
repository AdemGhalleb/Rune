"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Rune"
    app_version: str = "0.1.0"
    debug: bool = False

    # Bind to localhost only — single-user local app, no remote access.
    host: str = "127.0.0.1"
    port: int = 18742

    # Override in production/Tauri to OS-specific app data directory.
    data_dir: Path = Path(".rune")

    @property
    def log_dir(self) -> Path:
        return self.data_dir / "logs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
