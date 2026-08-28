import os
import datetime
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
    QProgressBar,
    QFrame,
    QGraphicsDropShadowEffect,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.widgets.folder_picker_widget import FolderPickerWidget
from MyVideoExplorer.db.db_scan import DbScanUtil
from MyVideoExplorer.db.db_scan_worker import ScanWorker


class SettingsMediaTab(SettingsBaseTab):
    sig_root_folders_changed = Signal(object)

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
        self._layout.addWidget(scroll)

    @property
    def layout(self) -> QVBoxLayout:
        return self._layout

    def _build_ui(self) -> None:
        # Dropdown
        db_dropdown_layout = QHBoxLayout()
        db_dropdown_layout.setContentsMargins(0, 0, 0, 0)
        db_dropdown_layout.setSpacing(5)
        db_dropdown_layout.addWidget(QLabel("Use Local DB:"))
        self.db_enabled_dropdown = QComboBox()
        self.db_enabled_dropdown.addItems(['Yes', 'No'])
        self.db_enabled_dropdown.setCurrentText('Yes' if self.state.db_enabled() else 'No')
        db_dropdown_layout.addWidget(self.db_enabled_dropdown)
        db_dropdown_layout.addStretch()

        self.content_layout.addLayout(db_dropdown_layout)

        self._update_db_tooltip()

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


    def _update_db_tooltip(self) -> None:
        has_db = self.state.db_enabled()
        if has_db:
            latest_date = None
            for folder_config in self.state.folder_configs:
                db_path = self.state.get_db_path(folder_config)
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

        for i, config in enumerate(self.state.folder_configs):
            browser = self._make_folder_browser(config)
            self.folder_nav_layout.addRow(browser)
            if i < len(self.state.folder_configs) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Sunken)
                self.folder_nav_layout.addRow(line)

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

        container = QFrame()
        container.setFrameShape(QFrame.Shape.StyledPanel)
        container.setObjectName("media_section_container")
        container.setStyleSheet(APP_THEME.media_section_container_qss())

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(10)
        shadow.setOffset(3, 3)
        shadow.setColor(Qt.GlobalColor.darkGray)
        container.setGraphicsEffect(shadow)

        outer_layout = QVBoxLayout(container)
        outer_layout.setContentsMargins(5, 5, 5, 5)
        outer_layout.setSpacing(2)

        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.addWidget(QLabel("Icon:"))
        row1.addWidget(icon_combo)
        row1.addSpacing(10)
        row1.addWidget(QLabel("Type:"))
        row1.addWidget(type_combo)
        row1.addSpacing(10)
        row1.addWidget(QLabel("Name:"))
        row1.addWidget(label_edit)
        row1.addStretch()
        row1.addWidget(remove_btn)

        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.addWidget(QLabel("Path:"))
        row2.addWidget(folder_edit)
        row2.addWidget(browse_btn)

        # Row 3 (Merged Stats + Scan)
        row3 = QHBoxLayout()
        row3.setContentsMargins(0, 5, 0, 0)

        db_path = self.state.get_db_path(folder_config)
        stats = None
        if os.path.exists(db_path):
            db_util = DbScanUtil(db_path)
            stats = db_util.get_stats(folder_config["path"])

        # stats: (folder_path, subfolders, files, images, videos, nfo, other, last_scanned)
        stats_icons = [
            "fa5s.folder",
            "fa5s.file",
            "fa5s.image",
            "fa5s.film",
            "fa5s.info-circle",
            "fa5s.file-alt",
            "fa5s.clock"
        ]
        icon_tooltips = {
            "fa5s.folder": "Subfolders",
            "fa5s.file": "Files",
            "fa5s.image": "Images",
            "fa5s.film": "Videos",
            "fa5s.info-circle": "NFO Files",
            "fa5s.file-alt": "Other Files",
            "fa5s.clock": "Last Scanned"
        }
        stats_data = [
            str(stats[1]) if stats else "-",
            str(stats[2]) if stats else "-",
            str(stats[3]) if stats else "-",
            str(stats[4]) if stats else "-",
            str(stats[5]) if stats else "-",
            str(stats[6]) if stats else "-",
            stats[7].strftime("%y-%m-%d %I%p").lower() if stats and stats[7] else "n/a"
        ]

        for i, (icon_name, val) in enumerate(zip(stats_icons, stats_data)):
            pair_layout = QHBoxLayout()
            pair_layout.setContentsMargins(0, 0, 0, 0)
            pair_layout.setSpacing(1)
            pair_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            lbl = QLabel(val)
            lbl.setObjectName(f"stats_val_{i}")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            # Make the last scanned label a bit wider
            if icon_name == "fa5s.clock":
                lbl.setFixedWidth(160)
            else:
                lbl.setFixedWidth(40)
            pair_layout.addWidget(lbl)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(APP_THEME.icon(icon_name, color=APP_THEME.text_color).pixmap(16, 16))
            icon_lbl.setToolTip(icon_tooltips.get(icon_name, ""))
            pair_layout.addWidget(icon_lbl)

            row3.addLayout(pair_layout)

            if i < len(stats_icons) - 1:
                row3.addSpacing(5)

        row3.addStretch()

        progress_bar = QProgressBar()
        progress_bar.setVisible(True)
        progress_bar.setFixedHeight(5)
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_bar.setFormat(" ")
        progress_bar.setStyleSheet(
            "QProgressBar { border: none; background: transparent; } "
            "QProgressBar::chunk { background: transparent; }"
        )

        scan_btn = QPushButton("Scan")
        scan_btn.setStyleSheet(APP_THEME.button_qss())
        scan_btn.setFixedWidth(scan_btn.sizeHint().width() + 20)

        scan_btn.clicked.connect(
            lambda: self._start_scan(folder_config, scan_btn, progress_bar)
        )
        row3.addWidget(scan_btn)

        row4 = QHBoxLayout()
        row4.setContentsMargins(0, 0, scan_btn.sizeHint().width(), 0)
        row4.addWidget(progress_bar)

        outer_layout.addLayout(row1)
        outer_layout.addLayout(row2)
        outer_layout.addLayout(row3)
        outer_layout.addLayout(row4)

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


    def _refresh_stats_labels(self, container: QWidget, folder_config: dict[str, Any]) -> None:
        db_path = self.state.get_db_path(folder_config)
        stats = None
        if os.path.exists(db_path):
            db_util = DbScanUtil(db_path)
            stats = db_util.get_stats(folder_config["path"])

        stats_data = [
            str(stats[1]) if stats else "-",
            str(stats[2]) if stats else "-",
            str(stats[3]) if stats else "-",
            str(stats[4]) if stats else "-",
            str(stats[5]) if stats else "-",
            str(stats[6]) if stats else "-",
            stats[7].strftime("%y-%m-%d %I%p").lower() if stats and stats[7] else "n/a"
        ]

        for i, val in enumerate(stats_data):
            lbl = container.findChild(QLabel, f"stats_val_{i}")
            if lbl:
                lbl.setText(val)

    def _start_scan(
        self,
        folder_config: dict[str, Any],
        scan_btn: QPushButton,
        progress_bar: QProgressBar,
    ) -> None:
        scan_btn.setEnabled(False)
        scan_btn.setText("0%")

        progress_bar.setFormat(" ")
        progress_bar.setStyleSheet(APP_THEME.progress_bar_qss(active=True))

        self.worker = ScanWorker(folder_config, self.file_util, self.nfo_util)
        self.worker.progress_init.connect(lambda val: progress_bar.setRange(0, val))
        self.worker.progress_updated.connect(progress_bar.setValue)
        self.worker.progress_updated.connect(
            lambda val: scan_btn.setText(f"{min(100, int(val / progress_bar.maximum() * 100))}%")
            if progress_bar.maximum() > 0
            else None
        )
        self.worker.finished.connect(
            lambda: self._on_scan_finished(scan_btn, progress_bar, folder_config)
        )
        self.worker.start()

    def _on_scan_finished(self, scan_btn: QPushButton, progress_bar: QProgressBar, folder_config: dict[str, Any]) -> None:
        progress_bar.setValue(0)
        progress_bar.setRange(0, 100)
        progress_bar.setFormat(" ")
        progress_bar.setStyleSheet(APP_THEME.progress_bar_qss(active=False))
        scan_btn.setText("Scan")
        scan_btn.setEnabled(True)

        container = scan_btn.parentWidget()
        if container:
            self._refresh_stats_labels(container, folder_config)


    def _save_media_settings(self) -> None:
        """Save only Media tab settings."""
        self.state._db_enabled = self.db_enabled_dropdown.currentText() == 'Yes'
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
        self.state.sig_settings_changed.emit(
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
