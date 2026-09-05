from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация из переменных окружения с префиксом GEOKZ_."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GEOKZ_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "GeoKZ API"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+asyncpg://geokz:geokz@localhost:5432/geokz"
    )
    sql_echo: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]

    # Opaque bearer sessions are stored only as SHA-256 token hashes in PostgreSQL.
    auth_session_hours: int = Field(default=12, ge=1, le=720)

    # Необязательный ключ бесплатного API Open Data Kazakhstan.
    # Отсутствие ключа не мешает работе локальной базы GeoKZ.
    egov_api_key: SecretStr | None = None
    external_http_timeout_seconds: float = Field(default=30.0, gt=0, le=300)

    # Dedicated external-sync worker periodically checks which AUTOMATIC sources are due.
    # Scheduler intentionally runs outside FastAPI workers to avoid duplicate background loops.
    external_scheduler_poll_seconds: int = Field(default=300, ge=30, le=3600)
    external_sync_failure_retry_hours: int = Field(default=6, ge=1, le=168)
    external_sync_running_timeout_hours: int = Field(default=6, ge=1, le=72)

    # Core Dataset online updates are optional. The channel is disabled until both an HTTPS
    # descriptor URL and at least one trusted Ed25519 public key are configured.
    core_dataset_update_manifest_url: str | None = None
    core_dataset_update_trusted_public_keys: dict[str, str] = Field(default_factory=dict)
    core_dataset_update_cache_dir: Path = Path("data/runtime/core_dataset_updates")
    core_dataset_update_max_bytes: int = Field(
        default=128 * 1024 * 1024,
        ge=1024 * 1024,
        le=2 * 1024 * 1024 * 1024,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
