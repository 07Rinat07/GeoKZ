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
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QInputDialog,
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
        except Exception as error:  # Qt worker boundary: surface failures to the UI thread.
            self.signals.failed.emit(str(error))
        else:
            self.signals.succeeded.emit(result)
        finally:
            self.signals.finished.emit()


class AsyncPage(QWidget):
    def __init__(
        self,
        client: GeoKZApiClient,
        language: DesktopLanguage,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
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


class LoginDialog(QDialog):
    def __init__(
        self,
        *,
        default_base_url: str,
        language: DesktopLanguage,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
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
        form.addRow("Language / Тіл / Язык", self.language_combo)

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
        if value not in {"ru", "kk", "en"}:
            return self.language
        return value

    def _login(self) -> None:
        base_url = self.server_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if not base_url or not username or not password:
            QMessageBox.warning(
                self,
                text(self.language, "error"),
                "API server, username and password are required.",
            )
            return

        candidate = GeoKZApiClient(base_url)
        self.buttons.setEnabled(False)

        def operation() -> object:
            return candidate.login(username, password)

        worker = ApiWorker(operation)
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
        self.refresh_button = QPushButton(text(language, "refresh"))
        self.update_all_button = QPushButton(text(language, "update_all"))
        self.refresh_button.clicked.connect(self.refresh)
        self.update_all_button.clicked.connect(self.update_all)

        help_label = QLabel(text(language, "help_data_sources"))
        help_label.setWordWrap(True)

        self.versions_box = QGroupBox(text(language, "versions"))
        versions_layout = QFormLayout(self.versions_box)
        self.application_version = QLabel("—")
        self.database_schema = QLabel("—")
        self.bundled_core = QLabel("—")
        self.installed_core = QLabel("—")
        versions_layout.addRow(text(language, "application_version"), self.application_version)
        versions_layout.addRow(text(language, "database_schema"), self.database_schema)
        versions_layout.addRow(text(language, "bundled_core_dataset"), self.bundled_core)
        versions_layout.addRow(text(language, "installed_core_dataset"), self.installed_core)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            [
                text(language, "data_sources"),
                text(language, "provider_version"),
                text(language, "source_status"),
                text(language, "last_success"),
                text(language, "last_error"),
                "Code",
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
        layout.addWidget(self.versions_box)
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

        def operation() -> object:
            return self.client.sync_all()

        def completed(_result: object) -> None:
            self.refresh()

        self.run_api(
            operation,
            completed,
            busy_widgets=(self.update_all_button, self.refresh_button),
        )

    def _apply_snapshot(self, value: object) -> None:
        if not isinstance(value, dict):
            self.show_error("Invalid Data Sources snapshot")
            return
        about = value.get("about")
        core = value.get("core")
        sources = value.get("sources")
        scheduler = value.get("scheduler")
        if not isinstance(about, dict) or not isinstance(core, dict) or not isinstance(sources, list):
            self.show_error("Invalid Data Sources API contract")
            return

        self.application_version.setText(str(about.get("version") or "—"))
        self.database_schema.setText(str(about.get("database_schema_version") or "—"))
        self.bundled_core.setText(str(about.get("core_dataset_version") or "—"))
        installed = core.get("installed")
        if isinstance(installed, dict):
            self.installed_core.setText(str(installed.get("dataset_version") or "—"))
        else:
            self.installed_core.setText("—")

        schedule_by_code: dict[str, JsonObject] = {}
        if isinstance(scheduler, dict):
            schedule_items = scheduler.get("sources")
            if isinstance(schedule_items, list):
                for item in schedule_items:
                    if isinstance(item, dict) and isinstance(item.get("source_code"), str):
                        schedule_by_code[item["source_code"]] = item

        self.table.setRowCount(len(sources))
        for row, source_value in enumerate(sources):
            if not isinstance(source_value, dict):
                continue
            code = str(source_value.get("code") or "")
            schedule = schedule_by_code.get(code, {})
            running = schedule.get("running_run_id")
            due = schedule.get("due")
            if running:
                source_status = "RUNNING"
            elif due is True:
                source_status = "DUE"
            elif source_value.get("last_error"):
                source_status = "ERROR"
            else:
                source_status = "READY"
            values = (
                source_value.get("display_name"),
                source_value.get("dataset_version"),
                source_status,
                source_value.get("last_success_at"),
                source_value.get("last_error"),
                code,
            )
            for column, cell in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(cell or "—")))


class FieldReviewPage(AsyncPage):
    def __init__(self, client: GeoKZApiClient, language: DesktopLanguage) -> None:
        super().__init__(client, language)
        self.queue: JsonObject | None = None
        self.current_record: JsonObject | None = None
        self.refresh_button = QPushButton(text(language, "refresh"))
        self.refresh_button.clicked.connect(self.refresh)
        self.help_label = QLabel(text(language, "help_field_review"))
        self.help_label.setWordWrap(True)
        self.policy_label = QLabel(text(language, "review_policy"))
        self.policy_label.setWordWrap(True)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([text(language, "field_review"), "Status", "Match"])
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.actions_widget = QWidget()
        self.actions_layout = QVBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.addStretch(1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.tree)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(self.details, 1)
        right_layout.addWidget(self.actions_widget)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.help_label)
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
            self.show_error("Invalid field-review queue")
            return
        self.queue = value
        policy = value.get("policy_note")
        if isinstance(policy, str):
            self.policy_label.setText(policy)
        self.tree.clear()
        records = value.get("records")
        if not isinstance(records, list):
            return
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            item = QTreeWidgetItem(
                [
                    str(record.get("display_name") or record.get("external_id") or "—"),
                    str(record.get("status") or "—"),
                    str(record.get("matching_status") or "—"),
                ]
            )
            item.setData(0, Qt.ItemDataRole.UserRole, index)
            candidates = record.get("candidates")
            if isinstance(candidates, list):
                for candidate_index, candidate in enumerate(candidates):
                    if not isinstance(candidate, dict):
                        continue
                    child = QTreeWidgetItem(
                        [
                            str(candidate.get("entity_display_name") or candidate.get("entity_id") or "—"),
                            str(candidate.get("status") or "—"),
                            str(candidate.get("match_method") or "—"),
                        ]
                    )
                    child.setData(0, Qt.ItemDataRole.UserRole, (index, candidate_index))
                    item.addChild(child)
            self.tree.addTopLevelItem(item)
        self.tree.expandAll()

    def _selection_changed(self) -> None:
        selected = self.tree.selectedItems()
        if not selected or self.queue is None:
            return
        records = self.queue.get("records")
        if not isinstance(records, list):
            return
        marker = selected[0].data(0, Qt.ItemDataRole.UserRole)
        record: JsonObject | None = None
        candidate: JsonObject | None = None
        if isinstance(marker, int) and 0 <= marker < len(records):
            raw_record = records[marker]
            if isinstance(raw_record, dict):
                record = raw_record
        elif isinstance(marker, tuple) and len(marker) == 2:
            record_index, candidate_index = marker
            if isinstance(record_index, int) and 0 <= record_index < len(records):
                raw_record = records[record_index]
                if isinstance(raw_record, dict):
                    record = raw_record
                    candidates = record.get("candidates")
                    if (
                        isinstance(candidates, list)
                        and isinstance(candidate_index, int)
                        and 0 <= candidate_index < len(candidates)
                        and isinstance(candidates[candidate_index], dict)
                    ):
                        candidate = candidates[candidate_index]
        if record is None:
            return
        self.current_record = record
        payload = {
            "record_id": record.get("record_id"),
            "external_id": record.get("external_id"),
            "matching_status": record.get("matching_status"),
            "raw_payload": record.get("raw_payload"),
            "normalized_payload": record.get("normalized_payload"),
            "selected_candidate": candidate,
        }
        self.details.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        actions = candidate.get("actions") if candidate is not None else record.get("actions")
        self._render_actions(actions if isinstance(actions, list) else [])

    def _render_actions(self, actions: list[object]) -> None:
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for action_value in actions:
            if not isinstance(action_value, dict):
                continue
            button = QPushButton(str(action_value.get("label") or action_value.get("code") or "Action"))
            button.setEnabled(action_value.get("enabled") is True)
            reason = action_value.get("disabled_reason")
            if isinstance(reason, str) and reason:
                button.setToolTip(reason)
            button.clicked.connect(
                lambda _checked=False, action=dict(action_value): self._execute_action(action)
            )
            self.actions_layout.addWidget(button)
        self.actions_layout.addStretch(1)

    def _execute_action(self, action: JsonObject) -> None:
        fields: list[str] = []
        for key in ("required_fields", "optional_fields"):
            value = action.get(key)
            if isinstance(value, list):
                fields.extend(item for item in value if isinstance(item, str))
        values: JsonObject = {}
        for field in fields:
            label = text(self.language, "entity_id") if field == "entity_id" else text(self.language, "comment")
            value, ok = QInputDialog.getText(self, str(action.get("label") or "Action"), label)
            if not ok:
                return
            if value.strip():
                values[field] = value.strip()
        self.run_api(
            lambda: self.client.execute_field_review_action(action, values=values),
            lambda _result: self.refresh(),
        )


class LicenseReviewPage(AsyncPage):
    def __init__(self, client: GeoKZApiClient, language: DesktopLanguage) -> None:
        super().__init__(client, language)
        self.records: list[JsonObject] = []
        self.refresh_button = QPushButton(text(language, "refresh"))
        self.accept_button = QPushButton(text(language, "accept"))
        self.reject_button = QPushButton(text(language, "reject"))
        self.refresh_button.clicked.connect(self.refresh)
        self.accept_button.clicked.connect(self.accept_selected)
        self.reject_button.clicked.connect(self.reject_selected)
        self.help_label = QLabel(text(language, "help_license_review"))
        self.help_label.setWordWrap(True)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["External ID", "Status", "Reviewer", "Comment"])
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
        layout.addWidget(self.help_label)
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
            self.show_error("Invalid license-review queue")
            return
        self.records = [dict(item) for item in value]
        self.table.setRowCount(len(self.records))
        for row, record in enumerate(self.records):
            values = (
                record.get("external_id"),
                record.get("status"),
                record.get("reviewed_by"),
                record.get("review_comment"),
            )
            for column, cell in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(cell or "—")))

    def _selected_record(self) -> JsonObject | None:
        row = self.table.currentRow()
        if 0 <= row < len(self.records):
            return self.records[row]
        return None

    def _selection_changed(self) -> None:
        record = self._selected_record()
        if record is None:
            self.details.clear()
            return
        self.details.setPlainText(json.dumps(record, ensure_ascii=False, indent=2, default=str))

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
        self.help_label = QLabel(text(language, "help_provenance"))
        self.help_label.setWordWrap(True)
        self.load_audit_button = QPushButton(text(language, "load_audit"))
        self.load_audit_button.clicked.connect(self.load_audit)
        self.load_audit_button.setEnabled(client.current_role == "admin")
        self.audit = QTextEdit()
        self.audit.setReadOnly(True)

        self.resource_type = QComboBox()
        self.resource_type.addItems(["source", "geological_entity", "fact"])
        self.resource_id = QLineEdit()
        self.load_revisions_button = QPushButton("Load revisions")
        self.load_revisions_button.clicked.connect(self.load_revisions)

        revision_form = QFormLayout()
        revision_form.addRow("Resource type", self.resource_type)
        revision_form.addRow("Resource UUID", self.resource_id)
        revision_form.addRow(self.load_revisions_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.help_label)
        layout.addWidget(self.load_audit_button)
        layout.addLayout(revision_form)
        layout.addWidget(self.audit, 1)

    def load_audit(self) -> None:
        self.run_api(
            lambda: self.client.audit_logs(limit=200),
            self._show_json,
            busy_widgets=(self.load_audit_button,),
        )

    def load_revisions(self) -> None:
        resource_id = self.resource_id.text().strip()
        if not resource_id:
            return
        resource_type = self.resource_type.currentText()
        self.run_api(
            lambda: self.client.revisions(resource_type, resource_id),
            self._show_json,
            busy_widgets=(self.load_revisions_button,),
        )

    def _show_json(self, value: object) -> None:
        self.audit.setPlainText(json.dumps(value, ensure_ascii=False, indent=2, default=str))


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
            f"{text(language, 'session_user')}: {user.get('display_name') or user.get('username') or '—'} | "
            f"{text(language, 'role')}: {user.get('role') or '—'}"
        )
        self.data_sources.refresh()
        self.field_review.refresh()
        self.license_review.refresh()

    def closeEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name.
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
    selected_language = login.selected_language
    window = GeoKZMainWindow(login.client, selected_language)
    window.show()
    return app.exec()
