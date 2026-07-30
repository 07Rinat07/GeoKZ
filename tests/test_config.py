from app.core.config import Settings


def test_default_api_prefix() -> None:
    settings = Settings(_env_file=None)
    assert settings.api_prefix == "/api/v1"
