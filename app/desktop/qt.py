from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.desktop.api_client import GeoKZApiClient, GeoKZApiError, JsonObject
from app.desktop.localization import DesktopLanguage, text


class WorkerSignals(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()


class ApiWorker(QRunnable):
    def __init__(self, operation: Callable[[], object]) -> None:
        super().__init__()
        self.operation = operation
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self.operation()
        except Exception as error:
            self.signals.failed.emit(str(error))
        else:
            self.signals.succeeded.emit(result)
        finally:
            self.signals.finished.emit()


class AsyncPage(QWidget):
    def __init__(self, client: GeoKZApiClient, language: DesktopLanguage) -> None:
        super().__init__()
        self.client = client
        self.language = language
        self.thread_pool = QThreadPool.globalInstance()
        self._workers: set[ApiWorker] = set()

    def run_api(
        self,
        operation: Callable[[], object],
        on_success: Callable[[object], None],
        *,
        busy_widgets: tuple[QWidget, ...] = (),
    ) -> None:
        for widget in busy_widgets:
            widget.setEnabled(False)
        worker = ApiWorker(operation)
        self._workers.add(worker)
        worker.signals.succeeded.connect(on_success)
        worker.signals.failed.connect(self.show_error)

        def cleanup() -> None:
            for widget in busy_widgets:
                widget.setEnabled(True)
            self._workers.discard(worker)

        worker.signals.finished.connect(cleanup)
        self.thread_pool.start(worker)

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, text(self.language, "error"), message)

    def invalid_contract(self) -> None:
        self.show_error(text(self.language, "invalid_api_contract"))


class LoginDialog(QDialog):
    def __init__(
        self,
        *,
        default_base_url: str,
        language: DesktopLanguage,
    ) -> None:
        super().__init__()
        self.language = language
        self.client: GeoKZApiClient | None = None
        self.thread_pool = QThreadPool.globalInstance()
        self._worker: ApiWorker | None = None
        self.setWindowTitle(text(language, "login_title"))
        self.setMinimumWidth(460)

        self.server_edit = QLineEdit(default_base_url)
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.language_combo = QComboBox()
        self.language_combo.addItem("Русский", "ru")
        self.language_combo.addItem("Қазақша", "kk")
        self.language_combo.addItem("English", "en")
        self.language_combo.setCurrentIndex({"ru": 0, "kk": 1, "en": 2}[language])

        form = QFormLayout()
        form.addRow(text(language, "server"), self.server_edit)
        form.addRow(text(language, "username"), self.username_edit)
        form.addRow(text(language, "password"), self.password_edit)
        form.addRow("RU / KK / EN", self.language_combo)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(text(language, "login"))
        self.buttons.accepted.connect(self._login)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.buttons)

    @property
    def selected_language(self) -> DesktopLanguage:
        value = self.language_combo.currentData()
        if value == "kk":
            return "kk"
        if value == "en":
            return "en"
        return "ru"

    def _login(self) -> None:
        base_url = self.server_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if not base_url or not username or not password:
            QMessageBox.warning(
                self,
                text(self.language, "error"),
                text(self.language, "credentials_required"),
            )
            return

        candidate = GeoKZApiClient(base_url)
        self.buttons.setEnabled(False)
        worker = ApiWorker(lambda: candidate.login(username, password))
        self._worker = worker

        def accepted(_result: object) -> None:
            self.client = candidate
            self.accept()

        def failed(message: str) -> None:
            candidate.close()
            QMessageBox.critical(self, text(self.language, "error"), message)

        def finished() -> None:
            self.buttons.setEnabled(True)
            self._worker = None

        worker.signals.succeeded.connect(accepted)
        worker.signals.failed.connect(failed)
        worker.signals.finished.connect(finished)
        self.thread_pool.start(worker)


class DataSourcesPage(AsyncPage):
    def __init__(self, client: GeoKZApiClient, language: DesktopLanguage) -> None:
        super().__init__(client, language)
        help_label = QLabel(text(language, "help_data_sources"))
        help_label.setWordWrap(True)

        self.refresh_button = QPushButton(text(language, "refresh"))
        self.update_all_button = QPushButton(text(language, "update_all"))
        self.refresh_button.clicked.connect(self.refresh)
        self.update_all_button.clicked.connect(self.update_all)

        self.application_version = QLabel("—")
        self.database_schema = QLabel("—")
        self.bundled_core = QLabel("—")
        self.installed_core = QLabel("—")
        versions = QGroupBox(text(language, "versions"))
        versions_layout = QFormLayout(versions)
        versions_layout.addRow(text(language, "application_version"), self.application_version)
        versions_layout.addRow(text(language, "database_schema"), self.database_schema)
        versions_layout.addRow(text(language, "bundled_core_dataset"), self.bundled_core)
        versions_layout.addRow(text(language, "installed_core_dataset"), self.installed_core)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            [
                text(language, "data_sources"),
                text(language, "provider_version"),
                text(language, "source_status"),
                text(language, "last_success"),
                text(language, "last_error"),
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        buttons = QHBoxLayout()
        buttons.addWidget(self.refresh_button)
        buttons.addWidget(self.update_all_button)
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(help_label)
        layout.addLayout(buttons)
        layout.addWidget(versions)
        layout.addWidget(self.table, 1)

    def refresh(self) -> None:
        def operation() -> object:
            return {
                "about": self.client.about(self.language),
                "core": self.client.core_dataset_status(),
                "sources": self.client.list_external_sources(self.language),
                "scheduler": self.client.scheduler_status(),
            }

        self.run_api(operation, self._apply_snapshot, busy_widgets=(self.refresh_button,))

    def update_all(self) -> None:
        answer = QMessageBox.question(
            self,
            text(self.language, "information"),
            text(self.language, "confirm_update_all"),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.run_api(
            self.client.sync_all,
            lambda _result: self.refresh(),
            busy_widgets=(self.update_all_button, self.refresh_button),
        )

    def _apply_snapshot(self, value: object) -> None:
        if not isinstance(value, dict):
            self.invalid_contract()
            return
        about = value.get("about")
        core = value.get("core")
        sources = value.get("sources")
        scheduler = value.get("scheduler")
        if not isinstance(about, dict) or not isinstance(core, dict) or not isinstance(sources, list):
            self.invalid_contract()
            return

        self.application_version.setText(str(about.get("version") or "—"))
        self.database_schema.setText(str(about.get("database_schema_version") or "—"))
        self.bundled_core.setText(str(about.get("core_dataset_version") or "—"))
        installed = core.get("installed")
        self.installed_core.setText(
            str(installed.get("dataset_version") or "—") if isinstance(installed, dict) else "—"
        )

        schedule_by_code: dict[str, JsonObject] = {}
        if isinstance(scheduler, dict):
            schedule_items = scheduler.get("sources")
            if isinstance(schedule_items, list):
                for item in schedule_items:
                    if isinstance(item, dict) and isinstance(item.get("source_code"), str):
                        schedule_by_code[item["source_code"]] = item

        rows = [item for item in sources if isinstance(item, dict)]
        self.table.setRowCount(len(rows))
        for row, source in enumerate(rows):
            code = str(source.get("code") or "")
            schedule = schedule_by_code.get(code, {})
            if schedule.get("running_run_id"):
                status = "RUNNING"
            elif schedule.get("due") is True:
                status = "DUE"
            elif source.get("last_error"):
                status = "ERROR"
            else:
                status = "READY"
            cells = (
                source.get("display_name"),
                source.get("dataset_version"),
                status,
                source.get("last_success_at"),
                source.get("last_error"),
            )
            for column, cell in enumerate(cells):
                self.table.setItem(row, column, QTableWidgetItem(str(cell or "—")))


class FieldReviewPage(AsyncPage):
    def __init__(self, client: GeoKZApiClient, language: DesktopLanguage) -> None:
        super().__init__(client, language)
        self.queue: JsonObject | None = None
        help_label = QLabel(text(language, "help_field_review"))
        help_label.setWordWrap(True)
        self.policy_label = QLabel(text(language, "review_policy"))
        self.policy_label.setWordWrap(True)
        self.refresh_button = QPushButton(text(language, "refresh"))
        self.refresh_button.clicked.connect(self.refresh)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([text(language, "field_review"), text(language, "source_status")])
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.action_panel = QWidget()
        self.action_layout = QVBoxLayout(self.action_panel)
        self.action_layout.setContentsMargins(0, 0, 0, 0)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(self.details, 1)
        right_layout.addWidget(self.action_panel)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.tree)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout(self)
        layout.addWidget(help_label)
        layout.addWidget(self.policy_label)
        layout.addWidget(self.refresh_button)
        layout.addWidget(splitter, 1)

    def refresh(self) -> None:
        self.run_api(
            lambda: self.client.field_review_queue(self.language, limit=200),
            self._apply_queue,
            busy_widgets=(self.refresh_button,),
        )

    def _apply_queue(self, value: object) -> None:
        if not isinstance(value, dict):
            self.invalid_contract()
            return
        records = value.get("records")
        if not isinstance(records, list):
            self.invalid_contract()
            return
        self.queue = value
        policy = value.get("policy_note")
        if isinstance(policy, str):
            self.policy_label.setText(policy)
        self.tree.clear()
        for record_index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            item = QTreeWidgetItem(
                [
                    str(record.get("display_name") or record.get("external_id") or "—"),
                    str(record.get("matching_status") or record.get("status") or "—"),
                ]
            )
            item.setData(0, Qt.ItemDataRole.UserRole, (record_index, -1))
            candidates = record.get("candidates")
            if isinstance(candidates, list):
                for candidate_index, candidate in enumerate(candidates):
                    if not isinstance(candidate, dict):
                        continue
                    child = QTreeWidgetItem(
                        [
                            str(candidate.get("entity_display_name") or candidate.get("entity_id") or "—"),
                            str(candidate.get("status") or candidate.get("match_method") or "—"),
                        ]
                    )
                    child.setData(
                        0,
                        Qt.ItemDataRole.UserRole,
                        (record_index, candidate_index),
                    )
                    item.addChild(child)
            self.tree.addTopLevelItem(item)
        self.tree.expandAll()

    def _selection_changed(self) -> None:
        selected = self.tree.selectedItems()
        if not selected or self.queue is None:
            return
        marker = selected[0].data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(marker, tuple) or len(marker) != 2:
            return
        records = self.queue.get("records")
        if not isinstance(records, list):
            return
        record_index, candidate_index = marker
        if not isinstance(record_index, int) or not 0 <= record_index < len(records):
            return
        record = records[record_index]
        if not isinstance(record, dict):
            return
        candidate: JsonObject | None = None
        if isinstance(candidate_index, int) and candidate_index >= 0:
            candidates = record.get("candidates")
            if (
                isinstance(candidates, list)
                and candidate_index < len(candidates)
                and isinstance(candidates[candidate_index], dict)
            ):
                candidate = candidates[candidate_index]
        payload = {
            "record_id": record.get("record_id"),
            "external_id": record.get("external_id"),
            "matching_status": record.get("matching_status"),
            text(self.language, "raw_payload"): record.get("raw_payload"),
            text(self.language, "normalized_payload"): record.get("normalized_payload"),
            "candidate": candidate,
        }
        self.details.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        actions = candidate.get("actions") if candidate is not None else record.get("actions")
        self._render_actions(actions if isinstance(actions, list) else [])

    def _render_actions(self, actions: list[object]) -> None:
        while self.action_layout.count():
            item = self.action_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for raw_action in actions:
            if not isinstance(raw_action, dict):
                continue
            action = dict(raw_action)
            button = QPushButton(str(action.get("label") or action.get("code") or "—"))
            button.setEnabled(action.get("enabled") is True)
            reason = action.get("disabled_reason")
            if isinstance(reason, str) and reason:
                button.setToolTip(reason)
            button.clicked.connect(
                lambda _checked=False, selected_action=action: self._execute_action(selected_action)
            )
            self.action_layout.addWidget(button)
        self.action_layout.addStretch(1)

    def _execute_action(self, action: JsonObject) -> None:
        required = action.get("required_fields")
        optional = action.get("optional_fields")
        fields = [
            field
            for values in (required, optional)
            if isinstance(values, list)
            for field in values
            if isinstance(field, str)
        ]
        payload: JsonObject = {}
        for field in fields:
            label_key = field if field in {"entity_id", "comment", "name_ru", "name_kk", "name_en"} else "comment"
            value, ok = QInputDialog.getText(
                self,
                str(action.get("label") or "GeoKZ"),
                text(self.language, label_key),
            )
            if not ok:
                return
            if value.strip():
                payload[field] = value.strip()
        self.run_api(
            lambda: self.client.execute_field_review_action(action, values=payload),
            lambda _result: self.refresh(),
        )


class LicenseReviewPage(AsyncPage):
    def __init__(self, client: GeoKZApiClient, language: DesktopLanguage) -> None:
        super().__init__(client, language)
        self.records: list[JsonObject] = []
        help_label = QLabel(text(language, "help_license_review"))
        help_label.setWordWrap(True)
        self.refresh_button = QPushButton(text(language, "refresh"))
        self.accept_button = QPushButton(text(language, "accept"))
        self.reject_button = QPushButton(text(language, "reject"))
        self.refresh_button.clicked.connect(self.refresh)
        self.accept_button.clicked.connect(self.accept_selected)
        self.reject_button.clicked.connect(self.reject_selected)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            ["ID", text(language, "source_status"), text(language, "comment")]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.details = QTextEdit()
        self.details.setReadOnly(True)

        buttons = QHBoxLayout()
        buttons.addWidget(self.refresh_button)
        buttons.addWidget(self.accept_button)
        buttons.addWidget(self.reject_button)
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(help_label)
        layout.addLayout(buttons)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.details, 1)

    def refresh(self) -> None:
        self.run_api(
            lambda: self.client.license_review_queue(limit=200),
            self._apply_records,
            busy_widgets=(self.refresh_button,),
        )

    def _apply_records(self, value: object) -> None:
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            self.invalid_contract()
            return
        self.records = [dict(item) for item in value]
        self.table.setRowCount(len(self.records))
        for row, record in enumerate(self.records):
            cells = (
                record.get("external_id"),
                record.get("status"),
                record.get("review_comment"),
            )
            for column, cell in enumerate(cells):
                self.table.setItem(row, column, QTableWidgetItem(str(cell or "—")))

    def _selected_record(self) -> JsonObject | None:
        row = self.table.currentRow()
        return self.records[row] if 0 <= row < len(self.records) else None

    def _selection_changed(self) -> None:
        record = self._selected_record()
        self.details.setPlainText(
            json.dumps(record, ensure_ascii=False, indent=2, default=str) if record else ""
        )

    def accept_selected(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        comment, ok = QInputDialog.getText(
            self,
            text(self.language, "accept"),
            text(self.language, "comment"),
        )
        if not ok:
            return
        record_id = str(record.get("record_id") or "")
        self.run_api(
            lambda: self.client.accept_license_record(record_id, comment.strip() or None),
            lambda _result: self.refresh(),
        )

    def reject_selected(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        comment, ok = QInputDialog.getText(
            self,
            text(self.language, "reject"),
            text(self.language, "comment"),
        )
        if not ok or not comment.strip():
            return
        record_id = str(record.get("record_id") or "")
        self.run_api(
            lambda: self.client.reject_license_record(record_id, comment.strip()),
            lambda _result: self.refresh(),
        )


class ProvenancePage(AsyncPage):
    def __init__(self, client: GeoKZApiClient, language: DesktopLanguage) -> None:
        super().__init__(client, language)
        help_label = QLabel(text(language, "help_provenance"))
        help_label.setWordWrap(True)
        self.audit_button = QPushButton(text(language, "load_audit"))
        self.audit_button.setEnabled(client.current_role == "admin")
        self.audit_button.clicked.connect(self.load_audit)
        self.resource_type = QComboBox()
        self.resource_type.addItems(["source", "geological_entity", "fact"])
        self.resource_id = QLineEdit()
        self.revisions_button = QPushButton(text(language, "load_revisions"))
        self.revisions_button.clicked.connect(self.load_revisions)
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        form = QFormLayout()
        form.addRow(text(language, "resource_type"), self.resource_type)
        form.addRow(text(language, "resource_id"), self.resource_id)
        form.addRow(self.revisions_button)

        layout = QVBoxLayout(self)
        layout.addWidget(help_label)
        layout.addWidget(self.audit_button)
        layout.addLayout(form)
        layout.addWidget(self.output, 1)

    def load_audit(self) -> None:
        self.run_api(
            lambda: self.client.audit_logs(limit=200),
            self._show_json,
            busy_widgets=(self.audit_button,),
        )

    def load_revisions(self) -> None:
        resource_id = self.resource_id.text().strip()
        if not resource_id:
            return
        resource_type = self.resource_type.currentText()
        self.run_api(
            lambda: self.client.revisions(resource_type, resource_id),
            self._show_json,
            busy_widgets=(self.revisions_button,),
        )

    def _show_json(self, value: object) -> None:
        self.output.setPlainText(json.dumps(value, ensure_ascii=False, indent=2, default=str))


class GeoKZMainWindow(QMainWindow):
    def __init__(self, client: GeoKZApiClient, language: DesktopLanguage) -> None:
        super().__init__()
        self.client = client
        self.language = language
        self.setWindowTitle(text(language, "app_title"))
        self.resize(1280, 820)

        self.tabs = QTabWidget()
        self.data_sources = DataSourcesPage(client, language)
        self.field_review = FieldReviewPage(client, language)
        self.license_review = LicenseReviewPage(client, language)
        self.provenance = ProvenancePage(client, language)
        self.tabs.addTab(self.data_sources, text(language, "data_sources"))
        self.tabs.addTab(self.field_review, text(language, "field_review"))
        self.tabs.addTab(self.license_review, text(language, "license_review"))
        self.tabs.addTab(self.provenance, text(language, "provenance"))
        self.setCentralWidget(self.tabs)

        user = client.current_user or {}
        self.statusBar().showMessage(
            f"{text(language, 'session_user')}: "
            f"{user.get('display_name') or user.get('username') or '—'} | "
            f"{text(language, 'role')}: {user.get('role') or '—'}"
        )
        self.data_sources.refresh()
        self.field_review.refresh()
        self.license_review.refresh()

    def closeEvent(self, event: Any) -> None:  # noqa: N802
        try:
            self.client.logout()
        except GeoKZApiError:
            pass
        finally:
            self.client.close()
        super().closeEvent(event)


def run_desktop(
    *,
    default_base_url: str = "http://127.0.0.1:8000",
    language: DesktopLanguage = "ru",
) -> int:
    app = QApplication.instance() or QApplication([])
    login = LoginDialog(default_base_url=default_base_url, language=language)
    if login.exec() != QDialog.DialogCode.Accepted or login.client is None:
        return 0
    window = GeoKZMainWindow(login.client, login.selected_language)
    window.show()
    return app.exec()
