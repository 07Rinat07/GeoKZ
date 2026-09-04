from functools import lru_cache
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

    # Необязательный ключ бесплатного API Open Data Kazakhstan.
    # Отсутствие ключа не мешает работе локальной базы GeoKZ.
    egov_api_key: SecretStr | None = None
    external_http_timeout_seconds: float = Field(default=30.0, gt=0, le=300)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
