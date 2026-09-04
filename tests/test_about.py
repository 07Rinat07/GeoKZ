from fastapi.testclient import TestClient

from app.main import app


def test_about_endpoint_supports_all_languages() -> None:
    expected_titles = {
        "ru": "GeoKZ — геологическая информационная система Казахстана",
        "kk": "GeoKZ — Қазақстанның геологиялық ақпараттық жүйесі",
        "en": "GeoKZ — Geological Information System of Kazakhstan",
    }

    with TestClient(app) as client:
        for language, expected_title in expected_titles.items():
            response = client.get("/api/v1/about", params={"lang": language})
            assert response.status_code == 200
            payload = response.json()
            assert payload["language"] == language
            assert payload["title"] == expected_title
            assert payload["author"] == "Sarmuldin Rinat"
            assert payload["email"] == "ura07srr@gmail.com"
            assert payload["supported_languages"] == ["ru", "kk", "en"]
