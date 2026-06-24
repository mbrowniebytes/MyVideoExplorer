import os
from typing import Any

from PySide6.QtCore import QSize, Qt, QTimer, Signal
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
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.settings.settings import SettingsBaseTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.folder_picker_widget import FolderPickerWidget


class SettingsMediaTab(SettingsBaseTab):
    sig_root_folders_changed = Signal(object)

    def __init__(
        self, state: SettingsState, log_util: LogUtil, parent: QWidget | None = None
    ) -> None:
        super().__init__(log_util, parent)
        self.state = state

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.main_widget = QWidget()
        self.content_layout = QVBoxLayout(self.main_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(15)

        self.folder_nav_group = QGroupBox()
        self.folder_nav_layout = QFormLayout()

        self._build_ui()
        self.content_layout.addStretch()

        scroll.setWidget(self.main_widget)
        self.layout.addWidget(scroll)

    def _build_ui(self) -> None:
        self.folder_nav_group = QGroupBox("Media Folders")
        self.folder_nav_group.setFont(
            QFont(APP_THEME.font_family, APP_THEME.font_size - 2)
        )
        self.folder_nav_layout = QFormLayout(self.folder_nav_group)

        self.folder_scroll_area = QScrollArea()
        self.folder_scroll_area.setWidgetResizable(True)
        self.folder_scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.folder_scroll_area.setWidget(self.folder_nav_group)

        self.folder_scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.folder_nav_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.content_layout.addWidget(self.folder_scroll_area, 1)

        self._refresh_folder_nav_settings()

        add_btn_layout = QHBoxLayout()
        add_btn_layout.addStretch()
        add_btn = QPushButton("Add Media Folder")
        add_btn.clicked.connect(self._add_folder)
        add_btn_layout.addWidget(add_btn)
        add_btn_layout.addStretch()

        self.content_layout.addLayout(add_btn_layout)

        self.content_layout.addStretch()

        save_btn_container = QWidget()
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.save_btn = QPushButton("Save Media Settings")
        self.save_btn.clicked.connect(self._save_media_settings)

        self.reset_btn = self._build_reset_button(
            "Reset Media Settings", self.reset_settings
        )

        spacer = QWidget()
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
        self.sig_saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Media Settings Reset",
                description="Media settings were reset to defaults.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        print("Media Settings reset")

    def _refresh_folder_nav_settings(self) -> None:
        try:
            if self.folder_nav_layout is None:
                return
            _ = self.folder_nav_layout.rowCount()
        except RuntimeError:
            return

        while self.folder_nav_layout.rowCount() > 0:
            self.folder_nav_layout.removeRow(0)

        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)

        h_row1 = QHBoxLayout()
        h_row1.setContentsMargins(0, 0, 0, 0)

        icon_header = QLabel("Icon")
        icon_header.setFixedWidth(40)
        icon_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_header = QLabel("Type")
        type_header.setFixedWidth(120)
        type_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_header.setToolTip("Media Type (Movie/Series)")
        name_header = QLabel("Name")
        name_header.setFixedWidth(200)

        header_font = QFont(
            APP_THEME.font_family, APP_THEME.font_size - 4, QFont.Weight.Bold
        )
        for lbl in [icon_header, type_header, name_header]:
            lbl.setFont(header_font)

        h_row1.addWidget(icon_header)
        h_row1.addWidget(type_header)
        h_row1.addWidget(name_header)
        h_row1.addStretch()

        remove_spacer = QWidget()
        remove_spacer.setFixedWidth(40)
        h_row1.addWidget(remove_spacer)

        header_layout.addLayout(h_row1)

        h_row2 = QHBoxLayout()
        h_row2.setContentsMargins(0, 0, 0, 0)

        dir_header = QLabel("Directory")
        dir_header.setFont(header_font)
        h_row2.addWidget(dir_header)
        h_row2.addStretch()

        browse_spacer = QWidget()
        browse_spacer.setFixedWidth(40)
        h_row2.addWidget(browse_spacer)

        header_layout.addLayout(h_row2)

        self.folder_nav_layout.addRow(header_container)

        if not self.state.folder_configs:
            msg = (
                "No media folders configured.\nClick the Add Media Folder button below."
            )
            instr = QLabel(msg)
            instr.setWordWrap(True)
            instr.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 4))
            instr.setStyleSheet(APP_THEME.label_qss("small"))
            self.folder_nav_layout.addRow(instr)
            return

        for config in self.state.folder_configs:
            browser = self._make_folder_browser(config)
            self.folder_nav_layout.addRow(browser)

    def _make_folder_browser(self, folder_config: dict[str, Any]) -> QWidget:
        default_folder = folder_config["path"]
        default_label = folder_config["label"]
        default_icon = folder_config.get("icon", "folder")
        default_media_type = folder_config.get("media_type", "movie")

        folder_picker = FolderPickerWidget(self)
        folder_picker.setVisible(False)
        folder_picker.selected_folder = default_folder

        folder_edit = QLineEdit(default_folder)
        folder_edit.setPlaceholderText("Media Folder Path")

        label_edit = QLineEdit(default_label)
        label_edit.setPlaceholderText("Label")
        label_edit.setFixedWidth(200)

        type_combo = QComboBox()
        type_combo.setFixedWidth(100)
        type_combo.addItem("Movie", "movie")
        type_combo.addItem("Series", "series")
        type_combo.setToolTip("Media Type: Movie or Series")

        type_index = type_combo.findData(default_media_type)
        if type_index >= 0:
            type_combo.setCurrentIndex(type_index)

        icon_combo = QComboBox()
        icon_combo.setFixedWidth(60)
        icon_combo.setIconSize(QSize(20, 20))
        standard_icons = [
            "fa5s.folder",
            "fa5s.folder-open",
            "fa5s.folder-minus",
            "fa5s.folder-plus",
            "fa5s.video",
            "fa5s.film",
            "fa5s.tv",
            "fa5s.star",
            "fa5s.heart",
            "fa5s.user",
            "fa5s.users",
            "fa5s.home",
            "fa5s.search",
            "fa5s.cog",
            "fa5s.list",
            "fa5s.th",
            "fa5s.image",
            "fa5s.images",
            "fa5s.file",
            "fa5s.file-video",
            "fa5s.camera",
            "fa5s.camera-retro",
            "fa5s.compact-disc",
            "fa5s.database",
            "fa5s.download",
            "fa5s.external-link-alt",
            "fa5s.eye",
            "fa5s.eye-slash",
            "fa5s.fire",
            "fa5s.flag",
            "fa5s.globe",
            "fa5s.info-circle",
            "fa5s.music",
            "fa5s.play-circle",
            "fa5s.rss",
            "fa5s.tag",
            "fa5s.tags",
        ]
        for icon_name in standard_icons:
            icon_combo.addItem(APP_THEME.icon(icon_name), "", icon_name)

        icon_index = icon_combo.findData(default_icon)
        if icon_index >= 0:
            icon_combo.setCurrentIndex(icon_index)

        remove_btn = QPushButton("")
        remove_btn.setIcon(APP_THEME.icon("fa5s.trash-alt", color=APP_THEME.text_color))
        remove_btn.setIconSize(QSize(APP_THEME.icon_size - 5, APP_THEME.icon_size - 5))
        remove_btn.setStyleSheet(APP_THEME.button_qss())
        remove_btn.clicked.connect(lambda: self._remove_folder(folder_config))

        browse_btn = QPushButton("")
        browse_btn.setIcon(
            APP_THEME.icon("fa5s.folder-open", color=APP_THEME.text_color)
        )
        browse_btn.setIconSize(QSize(APP_THEME.icon_size - 5, APP_THEME.icon_size - 5))
        browse_btn.setStyleSheet(APP_THEME.button_qss())
        browse_btn.clicked.connect(folder_picker.pick_folder)

        folder_picker.sig_selected_folder.connect(
            lambda payload: self._on_folder_selected(
                payload.data, folder_edit, folder_config
            )
        )

        container = QWidget()
        outer_layout = QVBoxLayout(container)
        outer_layout.setContentsMargins(0, 0, 0, 5)
        outer_layout.setSpacing(2)

        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.addWidget(icon_combo)
        row1.addWidget(type_combo)
        row1.addWidget(label_edit)
        row1.addStretch()
        row1.addWidget(remove_btn)

        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.addWidget(folder_edit)
        row2.addWidget(browse_btn)

        outer_layout.addLayout(row1)
        outer_layout.addLayout(row2)

        label_edit.editingFinished.connect(
            lambda le=label_edit: self._on_config_changed(
                folder_config, "label", le.text()
            )
        )
        type_combo.activated.connect(
            lambda: self._on_config_changed(
                folder_config, "media_type", type_combo.currentData()
            )
        )
        icon_combo.activated.connect(
            lambda: self._on_config_changed(
                folder_config, "icon", icon_combo.currentData()
            )
        )
        folder_edit.editingFinished.connect(
            lambda fe=folder_edit: self._on_config_changed(
                folder_config, "path", fe.text()
            )
        )

        return container

    def _has_valid_media_folders(self) -> bool:
        for cfg in self.state.folder_configs:
            p = cfg.get("path", "")
            if p and os.path.isdir(p):
                return True
        return False

    def _get_valid_media_paths(self) -> list[str]:
        valid_paths: list[str] = []
        for cfg in self.state.folder_configs:
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
        self, folder_config: dict[str, Any], key: str, value: Any
    ) -> None:
        if folder_config.get(key) == value:
            return
        folder_config[key] = value
        self._on_setting_changed()

        # paths = self._get_valid_media_paths()
        # self.sig_root_folders_changed.emit(paths)
        self._on_setting_changed()
        self.state.sig_settings_changed.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Media settings changed.",
                flow=SignalFlow.COMPONENT_INTERACTION,
            )
        )

    def _on_folder_selected(
        self, value: str, folder_edit: QLineEdit, folder_config: dict[str, Any]
    ) -> None:
        folder_edit.blockSignals(True)
        folder_edit.setText(value)
        folder_edit.blockSignals(False)
        folder_config["path"] = value
        self._on_setting_changed()
        paths = self._get_valid_media_paths()
        self.sig_root_folders_changed.emit(
            SignalPayload(
                data=paths,
                sender=self.__class__.__name__,
                name="Root Folders Changed",
                description="Media root folders were updated.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        self._on_setting_changed()

    def _add_folder(self) -> None:
        new_config = {
            "label": "New Media",
            "path": "",
            "icon": "folder",
            "media_type": "movie",
        }
        self.state.folder_configs.append(new_config)
        self._refresh_folder_nav_settings()

        self._on_setting_changed()

        paths = self._get_valid_media_paths()
        self.sig_root_folders_changed.emit(
            SignalPayload(
                data=paths,
                sender=self.__class__.__name__,
                name="Root Folders Changed",
                description="Media root folders were updated.",
                flow=SignalFlow.USER_INPUT,
            )
        )

        QTimer.singleShot(
            100,
            lambda: self._click_new_folder_label(new_config),
        )
        self.highlight_save_button()

    def _click_new_folder_label(self, folder_config: dict[str, Any]) -> None:
        item = self.folder_nav_layout.itemAt(self.folder_nav_layout.rowCount() - 1)
        if item is not None:
            widget = item.widget()
            for child in widget.findChildren(QLineEdit):
                if child.text() == "New Folder":
                    child.setFocus()
                    child.selectAll()
                    return

    def _remove_folder(self, folder_config: dict[str, Any]) -> None:
        label = folder_config.get("label", "")
        path = folder_config.get("path", "")

        reply = QMessageBox.question(
            self,
            "Confirm removal",
            f"Remove Media Folder config\n{label}: {path}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        if folder_config in self.state.folder_configs:
            self.state.folder_configs.remove(folder_config)

            self._refresh_folder_nav_settings()
            self._on_setting_changed()
            self.state.sig_settings_changed.emit(
                SignalPayload(
                    data=None,
                    sender=self.__class__.__name__,
                    name="Settings Changed",
                    description="Media settings changed.",
                    flow=SignalFlow.COMPONENT_INTERACTION,
                )
            )

            paths = self._get_valid_media_paths()
            self.sig_root_folders_changed.emit(
                SignalPayload(
                    data=paths,
                    sender=self.__class__.__name__,
                    name="Root Folders Changed",
                    description="Media root folders were updated.",
                    flow=SignalFlow.USER_INPUT,
                )
            )

        self.highlight_save_button()

    def _save_media_settings(self) -> None:
        """Save only Media tab settings."""
        self.state.save_media()
        self.reset_save_button()
        self.sig_saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Media Settings Saved",
                description="Media settings were saved.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        print("Media Settings saved")

    def apply_theme(self) -> None:
        super().apply_theme()
        # QTimer.singleShot(0, self._refresh_folder_nav_settings)
