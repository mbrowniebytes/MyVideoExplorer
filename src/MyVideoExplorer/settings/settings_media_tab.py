import os
import datetime
from typing import Any

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.settings.settings_media_folder_browser_section import SettingsMediaFolderBrowserSection


class SettingsMediaTab(SettingsBaseTab):
    root_folders_changed = Signal(object)

    def __init__(
        self,
        state: SettingsState,
        log_util: LogUtil,
        file_util: FileUtil,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(log_util, parent)
        self.state = state
        self.file_util = file_util
        self.nfo_util = NfoParseUtil(file_util, log_util)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.main_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.main_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(15)

        self.folder_nav_group = QGroupBox()
        self.folder_nav_layout = QFormLayout()

        self._build_ui()
        self.content_layout.addStretch()

        scroll.setWidget(self.main_widget)
        self._layout.addWidget(scroll)

    @property
    def layout(self) -> QVBoxLayout:
        return self._layout

    def _build_ui(self) -> None:
        # Dropdown
        db_dropdown_layout = QHBoxLayout()
        db_dropdown_layout.setContentsMargins(0, 0, 0, 0)
        db_dropdown_layout.setSpacing(5)
        lbl_db = QLabel("Use Local DB:", parent=self)
        db_dropdown_layout.addWidget(lbl_db)
        self.db_enabled_dropdown = QComboBox(self)
        self.db_enabled_dropdown.addItems(['Yes', 'No'])
        self.db_enabled_dropdown.setCurrentText('Yes' if self.state.db_enabled() else 'No')
        self.db_enabled_dropdown.currentIndexChanged.connect(self._on_db_enabled_changed)
        self.db_enabled_dropdown.currentIndexChanged.connect(self._on_setting_changed)
        db_dropdown_layout.addWidget(self.db_enabled_dropdown)
        db_dropdown_layout.addStretch()

        self.content_layout.addLayout(db_dropdown_layout)

        self._update_db_tooltip()

        self.folder_nav_group = QGroupBox("Media Folders")
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
        for text in ["Name", "", "Type", "Icon"]:
            if text:
                label = QLabel(text, parent=self)
                label.setStyleSheet(APP_THEME.label_qss("secondary"))
                label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 1))
                label.setContentsMargins(10, 0, 30, 0)
                header.addWidget(label)
            else:
                spacer = QWidget(self.folder_nav_content)
                spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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

        add_btn_layout = QHBoxLayout()
        add_btn_layout.addStretch()
        add_btn = QPushButton("Add Media Folder", parent=self)
        add_btn.clicked.connect(self._add_folder)
        add_btn_layout.addWidget(add_btn)
        add_btn_layout.addStretch()

        self.content_layout.addLayout(add_btn_layout)

        self.content_layout.addStretch()

        save_btn_container = QWidget(self)
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.save_btn = QPushButton("Save Media Settings", parent=self)
        self.save_btn.clicked.connect(self._save_media_settings)

        self.reset_btn = self._build_reset_button(
            "Reset Media Settings", self.reset_settings
        )

        spacer = QWidget(self)
        spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        save_btn_layout.addWidget(self.reset_btn)
        save_btn_layout.addWidget(spacer)
        save_btn_layout.addWidget(self.save_btn)
        self.content_layout.addWidget(
            save_btn_container,
            alignment=Qt.AlignmentFlag.AlignBottom,
        )

    def reset_settings(self) -> None:
        """Reset settings for this tab."""
        self.state.load_media()
        self._refresh_folder_nav_settings()
        self.reset_save_button()
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
        value = self.db_enabled_dropdown.currentText() == 'Yes'
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
                if os.path.exists(db_path):
                    mtime = os.path.getmtime(db_path)
                    date = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
                    if latest_date is None or date > latest_date:
                        latest_date = date

            latest_date_str = latest_date if latest_date else "Unknown"
            self.db_enabled_dropdown.setToolTip(
                f"Database filtering enabled (Latest update: {latest_date_str})."
            )
        else:
            self.db_enabled_dropdown.setToolTip(
                "Database filtering disabled. Filtering will be limited."
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
            msg = (
                "No media folders configured.\nClick the Add Media Folder button below."
            )
            instr = QLabel(msg, parent=self)
            instr.setWordWrap(True)
            instr.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 4))
            instr.setStyleSheet(APP_THEME.label_qss("small"))
            self.folder_nav_layout.addRow(instr)
            return

        for i, media_config in enumerate(self.state.media_configs):
            browser = SettingsMediaFolderBrowserSection(
                media_config, self.state.get_db_path, self.file_util, self.nfo_util
            )
            browser.config_changed.connect(self._on_config_changed)
            browser.remove_requested.connect(self._remove_folder)
            self.folder_nav_layout.addRow(browser)

    def _has_valid_media_folders(self) -> bool:
        for cfg in self.state.media_configs:
            p = cfg.get("path", "")
            if p and os.path.isdir(p):
                return True
        return False

    def _get_valid_media_paths(self) -> list[str]:
        valid_paths: list[str] = []
        for cfg in self.state.media_configs:
            p = cfg.get("path", "")
            if p:
                try:
                    real = os.path.realpath(p)
                except Exception:
                    continue
                if os.path.isdir(real):
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
        folder_edit.blockSignals(True)
        folder_edit.setText(value)
        folder_edit.blockSignals(False)
        media_config["path"] = value
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
                    if child.text() == "New Folder":
                        child.setFocus()
                        child.selectAll()
                        return

    def _remove_folder(self, media_config: dict[str, Any]) -> None:
        label = media_config.get("label", "")
        path = media_config.get("path", "")

        reply = QMessageBox.question(
            self,
            "Confirm removal",
            f"Remove Media Folder config\n{label}: {path}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        if media_config in self.state.media_configs:
            self.state.media_configs.remove(media_config)

            self._refresh_folder_nav_settings()
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
        for widget in self.folder_nav_content.findChildren(SettingsMediaFolderBrowserSection):
            widget.apply_changes()

        errors = self.state.validate_media_configs(self.state.media_configs)
        if isinstance(errors, list) and errors:
            QMessageBox.critical(
                self,
                "Invalid Media Settings",
                "<br>".join(errors),
            )
            return

        try:
            self.state.sync_db_file_names(self.state.media_configs)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(
                self,
                "Media DB Rename Error",
                str(exc),
            )
            return

        self.state._db_enabled = self.db_enabled_dropdown.currentText() == 'Yes'
        self.state.save_media()
        self.reset_save_button()

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
