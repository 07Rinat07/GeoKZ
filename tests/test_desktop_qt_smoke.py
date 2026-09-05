import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from app.desktop.api_client import GeoKZApiClient
from app.desktop.qt import DataSourcesPage, LoginDialog


def test_desktop_qt_shell_constructs_offscreen() -> None:
    app = QApplication.instance() or QApplication([])
    login = LoginDialog(default_base_url="http://127.0.0.1:8000", language="ru")
    assert login.windowTitle()
    assert login.selected_language == "ru"
    login.close()

    client = GeoKZApiClient("http://127.0.0.1:8000")
    page = DataSourcesPage(client, "en")
    assert page.refresh_button.text() == "Refresh"
    assert page.update_all_button.text() == "Update all"
    page.close()
    client.close()
    app.processEvents()
