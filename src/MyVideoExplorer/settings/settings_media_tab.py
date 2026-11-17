from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.app.app_version import (
    __version__ as app_version,
)
from MyVideoExplorer.app.app_version import (
    format_version_for_display,
)
from MyVideoExplorer.compare.compare_tab import CompareTab
from MyVideoExplorer.lang.lang_en import LangEn
from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.settings.settings_export import SettingsExportWorker
from MyVideoExplorer.settings.settings_import import SettingsImportWorker
from MyVideoExplorer.settings.settings_media_folder_browser_section import (
    SettingsMediaFolderBrowserSection,
)
from MyVideoExplorer.settings.settings_meta_tab import SettingsMetaTab
from MyVideoExplorer.settings.settings_state import (
    DEFAULT_SCAN_MEDIA_TIMEOUT_SECONDS,
    SCAN_MEDIA_TIMEOUT_OPTIONS,
    SettingsState,
)
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil, FileUtils
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.widgets.buttons.action_button import ActionButton
from MyVideoExplorer.widgets.combo_boxes.select_combo_box import SelectComboBox

if TYPE_CHECKING:
    from PySide6.QtWidgets import QProgressBar


class SettingsMediaTab(SettingsBaseTab):
    root_folders_changed = Signal(object)
    library_scan_succeeded = Signal(dict)

    def __init__(
        self,
        state: SettingsState,
        log_util: LogUtil,
        file_util: FileUtil,
        lang: LangEn,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(log_util, parent)
        self.state = state
        self.file_util = file_util
        self.lang = lang
        self.nfo_util = NfoParseUtil(file_util, log_util)

        self._export_worker: SettingsExportWorker | None = None
        self._import_worker: SettingsImportWorker | None = None
        self._export_btn: ActionButton
        self._import_btn: ActionButton
        self._progress_bar: QProgressBar | None = None

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 8, 0, 0)
        self._layout.setSpacing(0)

        # Separator line above sub-tabs
        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self._layout.addWidget(separator)

        self.tab_widget = QTabWidget(self)
        self._layout.addWidget(self.tab_widget)

        # Media sub-tab (existing content)
        self.media_tab = QWidget()
        self.media_scroll = QScrollArea(self.media_tab)
        self.media_scroll.setWidgetResizable(True)
        self.media_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        media_layout = QVBoxLayout(self.media_tab)
        media_layout.setContentsMargins(0, 0, 0, 0)
        media_layout.setSpacing(0)
        media_layout.addWidget(self.media_scroll)

        self.main_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.main_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(15)

        self.folder_nav_group = QGroupBox()
        self.folder_nav_layout = QFormLayout()

        self._build_ui()
        self.content_layout.addStretch()

        self.media_scroll.setWidget(self.main_widget)
        self.tab_widget.addTab(self.media_tab, "Media")

        # Meta sub-tab (new ffmpeg scan config)
        self.meta_tab = SettingsMetaTab(self.state, log_util, file_util, self.lang)
        self.tab_widget.addTab(self.meta_tab, "Meta")

        # Compare sub-tab (media comparison)
        self.compare_tab: CompareTab | None = None

    def set_compare_tab(self, compare_tab: CompareTab) -> None:
        """Set the compare tab and add it to the tab widget.

        Args:
            compare_tab: The compare tab widget.
        """
        self.compare_tab = compare_tab
        self.tab_widget.addTab(self.compare_tab, "Compare")

    def _build_ui(self) -> None:
        # Dropdown
        db_dropdown_layout = QHBoxLayout()
        db_dropdown_layout.setContentsMargins(0, 0, 0, 0)
        db_dropdown_layout.setSpacing(5)
        lbl_db = QLabel(self.lang.ui.settings.media.use_local_db, parent=self)
        db_dropdown_layout.addWidget(lbl_db)
        self.db_enabled_dropdown = SelectComboBox(self)
        self.db_enabled_dropdown.addItems(
            [self.lang.ui.settings.media.yes, self.lang.ui.settings.media.no]
        )
        self.db_enabled_dropdown.setCurrentText(
            self.lang.ui.settings.media.yes
            if self.state.db_enabled()
            else self.lang.ui.settings.media.no
        )
        self.db_enabled_dropdown.currentIndexChanged.connect(
            self._on_db_enabled_changed
        )
        self.db_enabled_dropdown.currentIndexChanged.connect(self._on_setting_changed)
        db_dropdown_layout.addWidget(self.db_enabled_dropdown)
        db_dropdown_layout.addStretch()

        self.scan_all_btn = ActionButton(
            self,
            icon_name="fa6s.rotate",
            tooltip=self.lang.ui.settings.media.scan_all_tooltip,
            text=self.lang.ui.settings.media.scan_all,
        )
        self.scan_all_btn.clicked.connect(self._on_scan_all_clicked)
        db_dropdown_layout.addWidget(self.scan_all_btn)

        self.content_layout.addLayout(db_dropdown_layout)

        self._update_db_tooltip()

        self.folder_nav_group = QGroupBox(self.lang.ui.settings.media.media_folders)
        self.folder_nav_group.setFont(
            QFont(APP_THEME.font_family, APP_THEME.font_size - 2)
        )
        folder_layout = QVBoxLayout()
        self.folder_nav_group.setLayout(folder_layout)
        folder_layout.setContentsMargins(0, 0, 0, 0)

        self.folder_nav_content = QWidget(self)
        self.folder_nav_layout = QFormLayout(self.folder_nav_content)

        # Header for the media sections
        header = QHBoxLayout()
        header.setContentsMargins(10, 0, 10, 0)
        for text in [
            self.lang.ui.settings.media.name_header,
            "",
            self.lang.ui.settings.media.type_header,
            self.lang.ui.settings.media.icon_header,
        ]:
            if text:
                label = QLabel(text, parent=self)
                label.setStyleSheet(APP_THEME.label_qss("secondary"))
                label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 1))
                label.setContentsMargins(10, 0, 30, 0)
                header.addWidget(label)
            else:
                spacer = QWidget(self.folder_nav_content)
                spacer.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                )
                header.addWidget(spacer)
        folder_layout.addLayout(header)

        line = QFrame(self)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(APP_THEME.separator_line_qss())
        folder_layout.addWidget(line)

        self.folder_scroll_area = QScrollArea(self)
        self.folder_scroll_area.setWidgetResizable(True)
        self.folder_scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.folder_scroll_area.setWidget(self.folder_nav_content)

        folder_layout.addWidget(self.folder_scroll_area)

        self.folder_scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.folder_nav_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.content_layout.addWidget(self.folder_nav_group, 1)

        self._refresh_folder_nav_settings()

        self.content_layout.addStretch()

        save_btn_container = QWidget(self)
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.reset_btn = self._build_reset_button(
            self.lang.ui.settings.media.reset_btn, self.reset_settings
        )

        add_btn = QPushButton(self.lang.ui.settings.media.add_media_folder, parent=self)
        add_btn.clicked.connect(self._add_folder)

        self.save_btn = QPushButton(self.lang.ui.settings.media.save_btn, parent=self)
        self.save_btn.clicked.connect(self._save_media_settings)

        save_btn_layout.addWidget(self.reset_btn)
        save_btn_layout.addStretch()

        self._export_btn = ActionButton(
            self,
            icon_name="fa6s.file-export",
            tooltip=self.lang.ui.settings.media.export_tooltip,
        )
        self._export_btn.clicked.connect(self._on_export_clicked)
        save_btn_layout.addWidget(self._export_btn)

        self._import_btn = ActionButton(
            self,
            icon_name="fa6s.file-import",
            tooltip=self.lang.ui.settings.media.import_tooltip,
        )
        self._import_btn.clicked.connect(self._on_import_clicked)
        save_btn_layout.addWidget(self._import_btn)

        save_btn_layout.addStretch()
        save_btn_layout.addWidget(add_btn)
        save_btn_layout.addStretch()
        save_btn_layout.addWidget(self.save_btn)
        self.content_layout.addWidget(
            save_btn_container,
            alignment=Qt.AlignmentFlag.AlignBottom,
        )

    # ---- Export / Import ----

    def _on_export_clicked(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.lang.ui.settings.media.export_title,
            "media_export.json",
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
        """Build the JSON payload for exporting media settings."""
        return {
            "app_version": format_version_for_display(app_version),
            "media_configs": self.state.media_configs,
            "db_enabled": self.state._db_enabled,
        }

    def _on_export_progress(self, current: int, total: int, label: str) -> None:
        self._show_progress(current, total)

    def _on_export_finished(self) -> None:
        self._hide_progress()
        self._export_worker = None
        self._set_export_import_enabled(True)
        QMessageBox.information(
            self,
            self.lang.ui.settings.media.export_complete,
            self.lang.ui.settings.media.export_complete_msg,
        )

    def _on_export_failed(self, error_msg: str) -> None:
        self._hide_progress()
        self._export_worker = None
        self._set_export_import_enabled(True)
        QMessageBox.critical(self, self.lang.ui.settings.media.export_failed, error_msg)

    def _on_import_clicked(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.lang.ui.settings.media.import_title,
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
        """Validate the structure of imported media settings data."""
        errors: list[str] = []
        if not isinstance(data, dict):
            return ["Import file must contain a JSON object."]
        media_configs = data.get("media_configs")
        if not isinstance(media_configs, list):
            return ["Import file must contain a 'media_configs' array."]
        seen_labels: set[str] = set()
        for idx, cfg in enumerate(media_configs):
            prefix = f"Media config {idx + 1}"
            if not isinstance(cfg, dict):
                errors.append(f"{prefix}: must be a JSON object.")
                continue
            label = cfg.get("label")
            if not label or not isinstance(label, str) or not label.strip():
                errors.append(f"{prefix}: missing or empty 'label'.")
            else:
                key = label.strip().casefold()
                if key in seen_labels:
                    errors.append(f"{prefix}: duplicate label '{label.strip()}'.")
                seen_labels.add(key)
            path = cfg.get("path")
            if not path or not isinstance(path, str) or not path.strip():
                errors.append(f"{prefix}: missing or empty 'path'.")
        db_enabled = data.get("db_enabled")
        if db_enabled is not None and not isinstance(db_enabled, bool):
            errors.append("'db_enabled' must be a boolean value.")
        return errors

    def _on_import_progress(self, current: int, total: int, label: str) -> None:
        self._show_progress(current, total)

    def _on_import_data_ready(self, data: dict[str, Any]) -> None:
        """Apply the validated import data to the media settings."""
        media_configs = data.get("media_configs", [])
        self.state.media_configs = media_configs
        self.state._normalize_media_config_paths()
        # Ensure each config has an icon
        for config in self.state.media_configs:
            if "icon" not in config:
                config["icon"] = "fa6s.folder"
            if "media_type" not in config:
                config["media_type"] = "movie"

        db_enabled = data.get("db_enabled")
        if isinstance(db_enabled, bool):
            self.state._db_enabled = db_enabled
            self.db_enabled_dropdown.setCurrentText(
                self.lang.ui.settings.media.yes
                if db_enabled
                else self.lang.ui.settings.media.no
            )

        self._refresh_folder_nav_settings()
        self.refresh_scan_targets()

    def _on_import_finished(self) -> None:
        self._hide_progress()
        self._import_worker = None
        self._set_export_import_enabled(True)
        QMessageBox.information(
            self,
            self.lang.ui.settings.media.import_complete,
            self.lang.ui.settings.media.import_complete_msg,
        )

    def _on_import_failed(self, error_msg: str) -> None:
        self._hide_progress()
        self._import_worker = None
        self._set_export_import_enabled(True)
        QMessageBox.critical(self, self.lang.ui.settings.media.import_failed, error_msg)

    def _set_export_import_enabled(self, enabled: bool) -> None:
        self._export_btn.setEnabled(enabled)
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

    def reset_settings(self) -> None:
        """Reset settings for this tab."""
        self.state.load_media()
        self._refresh_folder_nav_settings()
        self.reset_save_button()
        self.refresh_scan_targets()
        self.saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Media Settings Reset",
                description="Media settings were reset to defaults.",
                flow=SignalFlow.USER_INPUT,
            )
        )

    def _on_db_enabled_changed(self, index: int) -> None:
        value = (
            self.db_enabled_dropdown.currentText() == self.lang.ui.settings.media.yes
        )
        self.state._db_enabled = value

        self.state.settings_changed.emit(
            SignalPayload(
                data=value,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Use Local DB setting was changed.",
                flow=SignalFlow.USER_INPUT,
            )
        )

    def _update_db_tooltip(self) -> None:
        has_db = self.state.db_enabled()
        if has_db:
            latest_date = None
            for media_config in self.state.media_configs:
                db_path = self.state.get_db_path(media_config)
                if Path(db_path).exists():
                    mtime = Path(db_path).stat().st_mtime
                    date = (
                        dt.datetime.fromtimestamp(mtime, tz=dt.UTC)
                        .astimezone()
                        .strftime("%Y-%m-%d")
                    )
                    if latest_date is None or date > latest_date:
                        latest_date = date

            latest_date_str = latest_date or "Unknown"
            self.db_enabled_dropdown.setToolTip(
                self.lang.ui.settings.media.db_enabled_tooltip.format(
                    date=latest_date_str
                )
            )
        else:
            self.db_enabled_dropdown.setToolTip(
                self.lang.ui.settings.media.db_disabled_tooltip
            )

    def _refresh_folder_nav_settings(self) -> None:
        try:
            if self.folder_nav_layout is None:
                return
            _ = self.folder_nav_layout.rowCount()
        except RuntimeError:
            return

        while self.folder_nav_layout.rowCount() > 0:
            self.folder_nav_layout.removeRow(0)

        if not self.state.media_configs:
            msg = self.lang.ui.settings.media.no_media_folders_msg
            instr = QLabel(msg, parent=self)
            instr.setWordWrap(True)
            instr.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 4))
            instr.setStyleSheet(APP_THEME.label_qss("small"))
            self.folder_nav_layout.addRow(instr)
            self._refresh_scan_all_button_state()
            return

        for i, media_config in enumerate(self.state.media_configs):
            browser = SettingsMediaFolderBrowserSection(
                media_config,
                self.state.get_db_path,
                self.file_util,
                self.nfo_util,
                scan_timeout_seconds=self._get_scan_timeout_seconds,
            )
            browser.config_changed.connect(self._on_config_changed)
            browser.remove_requested.connect(self._remove_folder)
            browser.scan_succeeded.connect(self.library_scan_succeeded.emit)
            self.folder_nav_layout.addRow(browser)

        self._refresh_scan_all_button_state()

    def _get_scan_timeout_seconds(self) -> int:
        timeout = getattr(
            self.state, "scan_media_timeout_seconds", DEFAULT_SCAN_MEDIA_TIMEOUT_SECONDS
        )
        return (
            timeout
            if isinstance(timeout, int) and timeout in SCAN_MEDIA_TIMEOUT_OPTIONS
            else DEFAULT_SCAN_MEDIA_TIMEOUT_SECONDS
        )

    def _has_valid_media_folders(self) -> bool:
        for cfg in self.state.media_configs:
            p = cfg.get("path", "")
            if p and Path(p).is_dir():
                return True
        return False

    def _refresh_scan_all_button_state(self) -> None:
        if not hasattr(self, "scan_all_btn"):
            return
        if getattr(self, "_scan_all_active", False):
            return
        self.scan_all_btn.setEnabled(self._has_valid_media_folders())

    def _on_scan_all_clicked(self) -> None:
        sections = self.folder_nav_content.findChildren(
            SettingsMediaFolderBrowserSection
        )
        valid_sections = [
            s
            for s in sections
            if str(s.media_config.get("label", "")).strip()
            and str(s.media_config.get("path", "")).strip()
            and Path(str(s.media_config.get("path", ""))).is_dir()
        ]

        if not valid_sections:
            QMessageBox.information(
                self,
                self.lang.ui.settings.media.scan_all,
                self.lang.ui.settings.media.scan_all_no_folders,
            )
            return

        self._scan_all_queue = list(valid_sections)
        self._scan_all_total = len(valid_sections)
        self._scan_all_current = 0
        self._scan_all_active = True
        self.scan_all_btn.setEnabled(False)
        self._run_next_scan_all()

    def _run_next_scan_all(self) -> None:
        if not getattr(self, "_scan_all_queue", None):
            self._scan_all_active = False
            self.scan_all_btn.setEnabled(self._has_valid_media_folders())
            self.scan_all_btn.setText(self.lang.ui.settings.media.scan_all)
            self.scan_all_btn.set_action_icon("fa6s.rotate")
            self._update_db_tooltip()
            return

        self._scan_all_current += 1
        section = self._scan_all_queue.pop(0)
        self.scan_all_btn.setText(
            self.lang.ui.settings.media.scanning.format(
                current=self._scan_all_current, total=self._scan_all_total
            )
        )
        self.folder_scroll_area.ensureWidgetVisible(section.progress_bar, 12, 24)

        def on_section_finished():
            try:
                section.scan_finished.disconnect(on_section_finished)
            except RuntimeError, TypeError:
                pass
            try:
                section.scan_stalled.disconnect(on_section_stalled)
            except RuntimeError, TypeError:
                pass
            self._run_next_scan_all()

        def on_section_stalled():
            self.scan_all_btn.setText(
                self.lang.ui.settings.media.stopping_stalled.format(
                    current=self._scan_all_current, total=self._scan_all_total
                )
            )

        section.scan_finished.connect(on_section_finished)
        section.scan_stalled.connect(on_section_stalled)
        if not section.start_scan():
            on_section_finished()

    def _get_valid_media_paths(self) -> list[str]:
        valid_paths: list[str] = []
        for cfg in self.state.media_configs:
            p = cfg.get("path", "")
            if p:
                try:
                    real = FileUtils.resolve_path(p)
                except Exception:
                    continue
                if Path(real).is_dir():
                    valid_paths.append(real)
        return valid_paths

    def _on_config_changed(
        self, media_config: dict[str, Any], key: str, value: Any
    ) -> None:
        if media_config.get(key) == value:
            return
        media_config[key] = value
        self._on_setting_changed()

    def _on_folder_selected(
        self, value: str, folder_edit: QLineEdit, media_config: dict[str, Any]
    ) -> None:
        normalized_value = FileUtils.normalize_path(value)
        folder_edit.blockSignals(True)
        folder_edit.setText(normalized_value)
        folder_edit.blockSignals(False)
        media_config["path"] = normalized_value
        self._on_setting_changed()

    def _add_folder(self) -> None:
        new_config = {
            "label": "",
            "path": "",
            "icon": "fa6s.folder",
            "media_type": "movie",
        }
        self.state.media_configs.append(new_config)
        self._refresh_folder_nav_settings()
        self.refresh_scan_targets()

        self._on_setting_changed()

        QTimer.singleShot(
            100,
            lambda: self._click_new_folder_label(new_config),
        )
        self.highlight_save_button()

    def _click_new_folder_label(self, folder_config: dict[str, Any]) -> None:
        item = self.folder_nav_layout.itemAt(self.folder_nav_layout.rowCount() - 1)
        if item is not None:
            widget = item.widget()
            if widget is not None:
                for child in widget.findChildren(QLineEdit):
                    if child.text() == self.lang.ui.settings.media.new_folder:
                        child.setFocus()
                        child.selectAll()
                        return

    def _remove_folder(self, media_config: dict[str, Any]) -> None:
        label = media_config.get("label", "")
        path = media_config.get("path", "")

        reply = QMessageBox.question(
            self,
            self.lang.ui.settings.media.confirm_removal,
            self.lang.ui.settings.media.confirm_removal_msg.format(
                label=label, path=path
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        if media_config in self.state.media_configs:
            self.state.media_configs.remove(media_config)

            self._refresh_folder_nav_settings()
            self.refresh_scan_targets()
            self._on_setting_changed()
            self.state.settings_changed.emit(
                SignalPayload(
                    data=None,
                    sender=self.__class__.__name__,
                    name="Settings Changed",
                    description="Media settings changed.",
                    flow=SignalFlow.COMPONENT_INTERACTION,
                )
            )

        self.highlight_save_button()

    def _save_media_settings(self) -> None:
        """Save only Media tab settings."""
        # Force apply changes from all browser sections
        for widget in self.folder_nav_content.findChildren(
            SettingsMediaFolderBrowserSection
        ):
            widget.apply_changes()

        errors = self.state.validate_media_configs(self.state.media_configs)
        if isinstance(errors, list) and errors:
            QMessageBox.critical(
                self,
                self.lang.ui.settings.media.invalid_media_settings,
                "<br>".join(errors),
            )
            return

        try:
            self.state.sync_db_file_names(self.state.media_configs)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(
                self,
                self.lang.ui.settings.media.media_db_rename_error,
                str(exc),
            )
            return

        self.state._db_enabled = (
            self.db_enabled_dropdown.currentText() == self.lang.ui.settings.media.yes
        )
        self.state.save_media()
        self.reset_save_button()

        # Refresh Meta tab scan targets after saving
        self.refresh_scan_targets()

        paths = self._get_valid_media_paths()
        self.root_folders_changed.emit(
            SignalPayload(
                data=paths,
                sender=self.__class__.__name__,
                name="Root Folders Changed",
                description="Media root folders were updated.",
                flow=SignalFlow.USER_INPUT,
            )
        )

        self.saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Media Settings Saved",
                description="Media settings were saved.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        self.state.settings_changed.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Media Settings Saved",
                description="Media settings were saved.",
                flow=SignalFlow.COMPONENT_INTERACTION,
            )
        )
        self._update_db_tooltip()

    def apply_theme(self) -> None:
        super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.setFont(font)
        if hasattr(self, "meta_tab"):
            self.meta_tab.apply_theme()

    def closeEvent(self, event) -> None:
        """Clean up workers on tab close."""
        if self._export_worker is not None and self._export_worker.isRunning():
            self._export_worker.requestInterruption()
        if self._import_worker is not None and self._import_worker.isRunning():
            self._import_worker.requestInterruption()
        super().closeEvent(event)

    def refresh_scan_targets(self) -> None:
        """Repopulate the scan target dropdown in the Meta tab when media configs change."""
        if hasattr(self, "meta_tab"):
            self.meta_tab.refresh_scan_targets()
