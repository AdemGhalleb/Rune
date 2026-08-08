"""Application configuration."""

import os
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

    # Keep runtime data outside the source tree. Tests can override this setting.
    data_dir: Path = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local")) / "Rune"

    @property
    def log_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "rune.db"

    @property
    def database_url(self) -> str:
        return f"sqlite+pysqlite:///{self.database_path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
