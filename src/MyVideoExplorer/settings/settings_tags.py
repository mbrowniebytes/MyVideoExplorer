from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QWidget

from MyVideoExplorer.db.db_tags import DbTags
from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.settings.settings_export import SettingsExportWorker
from MyVideoExplorer.settings.settings_import import SettingsImportWorker
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.tag_cloud.tag_cloud_settings import TagCloudSettings
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.buttons.action_button import ActionButton

if TYPE_CHECKING:
    from PySide6.QtWidgets import QProgressBar


class SettingsTagsTab(SettingsBaseTab):
    """Settings tab for managing tags, with export and import support."""

    def __init__(
        self,
        state: SettingsState,
        log_util: LogUtil,
        tag_store: DbTags | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(log_util, parent)
        self.state = state
        self.tag_store = tag_store
        self.tag_cloud_settings = TagCloudSettings(state, tag_store, self)

        self._export_worker: SettingsExportWorker | None = None
        self._import_worker: SettingsImportWorker | None = None
        self._export_btn: ActionButton | None = None
        self._import_btn: ActionButton | None = None
        self._progress_bar: QProgressBar | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(self.tag_cloud_settings)
        layout.addStretch(1)

        # --- Add export/import buttons to the tag cloud controls row ---
        self._export_btn = ActionButton(
            self, icon_name="fa6s.file-export", tooltip="Export tags to JSON"
        )
        self._export_btn.clicked.connect(self._on_export_clicked)
        self.tag_cloud_settings.cloud.add_control_widget(self._export_btn)

        self._import_btn = ActionButton(
            self, icon_name="fa6s.file-import", tooltip="Import tags from JSON"
        )
        self._import_btn.clicked.connect(self._on_import_clicked)
        self.tag_cloud_settings.cloud.add_control_widget(self._import_btn)

    # ---- Export / Import ----

    def _on_export_clicked(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Tags",
            "tags_export.json",
            "JSON Files (*.json)",
        )
        if not file_path:
            return
        self._set_export_import_enabled(False)
        worker = SettingsExportWorker(self._build_export_data, Path(file_path))
        self._export_worker = worker
        worker.progress.connect(self._on_export_progress)
        worker.finished.connect(self._on_export_finished)
        worker.failed.connect(self._on_export_failed)
        worker.start()

    def _build_export_data(self) -> dict[str, Any]:
        """Build the JSON payload for exporting all tags."""
        tags = self._get_tags()
        return {"tags": tags}

    def _get_tags(self) -> list[dict[str, str]]:
        """Return the current list of tags from the tag store or state."""
        if self.tag_store is not None:
            return self.tag_store.list_tags()
        return list(self.state.tags)

    def _on_export_progress(self, current: int, total: int, label: str) -> None:
        self._show_progress(current, total)

    def _on_export_finished(self) -> None:
        self._hide_progress()
        self._export_worker = None
        self._set_export_import_enabled(True)
        QMessageBox.information(self, "Export Complete", "Tags exported successfully.")

    def _on_export_failed(self, error_msg: str) -> None:
        self._hide_progress()
        self._export_worker = None
        self._set_export_import_enabled(True)
        QMessageBox.critical(self, "Export Failed", error_msg)

    def _on_import_clicked(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Tags",
            "",
            "JSON Files (*.json)",
        )
        if not file_path:
            return
        self._set_export_import_enabled(False)
        worker = SettingsImportWorker(Path(file_path), self._validate_import_data)
        self._import_worker = worker
        worker.progress.connect(self._on_import_progress)
        worker.data_ready.connect(self._on_import_data_ready)
        worker.failed.connect(self._on_import_failed)
        worker.finished.connect(self._on_import_finished)
        worker.start()

    def _validate_import_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the structure of imported tag data."""
        errors: list[str] = []
        if not isinstance(data, dict):
            return ["Import file must contain a JSON object."]
        tags = data.get("tags")
        if not isinstance(tags, list):
            return ["Import file must contain a 'tags' array."]
        seen: set[str] = set()
        for idx, t in enumerate(tags):
            prefix = f"Tag {idx + 1}"
            name = t.get("tag")
            if not name or not isinstance(name, str) or not name.strip():
                errors.append(f"{prefix}: missing or empty 'tag'.")
                continue
            key = name.strip().casefold()
            if key in seen:
                errors.append(f"{prefix}: duplicate tag name '{name.strip()}'.")
            seen.add(key)
            color = t.get("color")
            if color is not None:
                if not isinstance(color, str) or not color.strip():
                    errors.append(f"{prefix}: invalid 'color' value.")
        return errors

    def _on_import_progress(self, current: int, total: int, label: str) -> None:
        self._show_progress(current, total)

    def _on_import_data_ready(self, data: dict[str, Any]) -> None:
        """Apply the validated import data to the tag store."""
        tags_data = data.get("tags", [])
        if self.tag_store is not None:
            self._import_to_store(tags_data, self.tag_store)
        else:
            self._import_to_state(tags_data)
        # Refresh the tag cloud display
        if hasattr(self.tag_cloud_settings, "refresh"):
            self.tag_cloud_settings.refresh()

    def _import_to_store(
        self, tags_data: list[dict[str, Any]], tag_store: DbTags
    ) -> None:
        """Import tags into the DbTags store, treating duplicates as updates."""
        existing = tag_store.list_tags()
        existing_map: dict[str, str] = {t["tag"].casefold(): t["tag"] for t in existing}
        for t in tags_data:
            name = t.get("tag", "").strip()
            color = t.get("color", "#808080")
            if not name:
                continue
            if name.casefold() in existing_map:
                # Update existing tag's color
                tag_store.set_tag_color(name, color)
            else:
                # Add new tag
                tag_store.add_catalog_tag(name, color)

    def _import_to_state(self, tags_data: list[dict[str, Any]]) -> None:
        """Import tags into the in-memory state, treating duplicates as updates."""
        current = list(self.state.tags)
        current_map: dict[str, int] = {
            t["tag"].casefold(): i for i, t in enumerate(current)
        }
        for t in tags_data:
            name = t.get("tag", "").strip()
            color = t.get("color", "#808080")
            if not name:
                continue
            if name.casefold() in current_map:
                # Update existing tag
                idx = current_map[name.casefold()]
                current[idx] = {"tag": current[idx]["tag"], "color": color}
            else:
                # Add new tag
                current.append({"tag": name, "color": color})
                current_map[name.casefold()] = len(current) - 1
        self.state.set_tags(current)

    def _on_import_finished(self) -> None:
        self._hide_progress()
        self._import_worker = None
        self._set_export_import_enabled(True)
        QMessageBox.information(self, "Import Complete", "Tags imported successfully.")

    def _on_import_failed(self, error_msg: str) -> None:
        self._hide_progress()
        self._import_worker = None
        self._set_export_import_enabled(True)
        QMessageBox.critical(self, "Import Failed", error_msg)

    def _set_export_import_enabled(self, enabled: bool) -> None:
        if self._export_btn is not None:
            self._export_btn.setEnabled(enabled)
        if self._import_btn is not None:
            self._import_btn.setEnabled(enabled)

    def _show_progress(self, current: int, total: int) -> None:
        from PySide6.QtWidgets import QProgressBar

        if self._progress_bar is None:
            self._progress_bar = QProgressBar(self)
            layout = QVBoxLayout(self)
            layout.insertWidget(0, self._progress_bar)
        self._progress_bar.show()
        self._progress_bar.setMaximum(max(total, 1))
        self._progress_bar.setValue(current)

    def _hide_progress(self) -> None:
        if self._progress_bar is not None:
            self._progress_bar.hide()

    def apply_theme(self) -> None:
        super().apply_theme()
        self.setStyleSheet(APP_THEME.container_qss())
