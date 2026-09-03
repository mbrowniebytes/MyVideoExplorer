import os
import re
from typing import Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.db.db_scan import DbScanUtil
from MyVideoExplorer.db.db_scan_worker import ScanWorker
from MyVideoExplorer.lang.lang_loader import LangLoader
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.widgets.folder_picker_widget import FolderPickerWidget


class SettingsMediaFolderBrowserSection(QFrame, ThemableMixin):
    config_changed = Signal(dict, str, Any)
    remove_requested = Signal(dict)

    def __init__(
        self,
        media_config: dict[str, Any],
        get_db_path_callback: Any,
        file_util: FileUtil,
        nfo_util: NfoParseUtil,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.media_config = media_config
        self.get_db_path_callback = get_db_path_callback
        self.file_util = file_util
        self.nfo_util = nfo_util
        self.lang = LangLoader.get_lang("en")
        self.worker = None

        self._build_ui()
        self.apply_theme()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Configuration UI (Label, Type, Icon, Path)
        row1_layout = QHBoxLayout()
        row1_layout.setContentsMargins(0, 0, 0, 0)

        self.label_edit = QLineEdit(self.media_config.get("label", ""), parent=self)
        self.label_edit.setPlaceholderText("Media Name")
        self.label_edit.textChanged.connect(self._refresh_scan_button_state)
        self.label_edit.editingFinished.connect(
            lambda: self.config_changed.emit(self.media_config, "label", self.label_edit.text())
        )
        row1_layout.addWidget(self.label_edit)

        self.type_combo = QComboBox(self)
        self.type_combo.addItem("Movie", "movie")
        self.type_combo.addItem("Series", "series")
        current_type = self.media_config.get("media_type", "movie")
        index = self.type_combo.findData(current_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        self.type_combo.currentTextChanged.connect(
            lambda text: self.config_changed.emit(self.media_config, "media_type", self.type_combo.currentData())
        )
        row1_layout.addWidget(self.type_combo)

        # Delete button
        self.remove_btn = QPushButton(parent=self)
        self.remove_btn.setIcon(APP_THEME.icon("fa6s.xmark"))
        self.remove_btn.setStyleSheet(APP_THEME.button_qss())
        self.remove_btn.setFixedWidth(30)
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.media_config))

        standard_icons = [
            "fa6s.folder",
            "fa6s.folder-open",
            "fa6s.folder-minus",
            "fa6s.folder-plus",
            "fa6s.video",
            "fa6s.film",
            "fa6s.tv",
            "fa6s.star",
            "fa6s.heart",
            "fa6s.user",
            "fa6s.users",
            "fa6s.home",
            "fa6s.search",
            "fa6s.cog",
            "fa6s.list",
            "fa6s.th",
            "fa6s.image",
            "fa6s.images",
            "fa6s.file",
            "fa6s.file-video",
            "fa6s.camera",
            "fa6s.camera-retro",
            "fa6s.compact-disc",
            "fa6s.database",
            "fa6s.download",
            "fa6s.external-link-alt",
            "fa6s.eye",
            "fa6s.eye-slash",
            "fa6s.fire",
            "fa6s.flag",
            "fa6s.globe",
            "fa6s.info-circle",
            "fa6s.music",
            "fa6s.play-circle",
            "fa6s.rss",
            "fa6s.tag",
            "fa6s.tags",
        ]
        self.icon_combo = QComboBox(self)
        for icon_name in standard_icons:
            self.icon_combo.addItem(APP_THEME.icon(icon_name), "", icon_name)

        current_icon = self.media_config.get("icon", "fa6s.folder")
        index = self.icon_combo.findData(current_icon)
        if index >= 0:
            self.icon_combo.setCurrentIndex(index)
        self.icon_combo.currentIndexChanged.connect(
            lambda index: self.config_changed.emit(self.media_config, "icon", self.icon_combo.itemData(index))
        )
        row1_layout.addWidget(self.icon_combo)

        layout.addLayout(row1_layout)

        self.folder_picker = FolderPickerWidget(self)
        self.folder_picker.setVisible(False)
        self.folder_picker.selected_folder = self.media_config["path"]
        self.folder_picker.sig_selected_folder.connect(
            lambda payload: self._on_folder_selected(payload.data)
        )

        self.folder_edit = QLineEdit(self.media_config["path"], parent=self)
        self.folder_edit.setPlaceholderText("Media Path")
        self.folder_edit.textChanged.connect(self._refresh_scan_button_state)
        self.folder_edit.editingFinished.connect(
            lambda: self.config_changed.emit(self.media_config, "path", self.folder_edit.text())
        )

        browse_btn = QPushButton("Browse", parent=self)
        browse_btn.clicked.connect(self.folder_picker.pick_folder)

        row2_layout = QHBoxLayout()
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.addWidget(self.folder_edit)
        row2_layout.addWidget(browse_btn)
        row2_layout.addSpacing(10)
        row2_layout.addWidget(self.remove_btn)

        layout.addLayout(row2_layout)

        # Stats + Scan UI
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setContentsMargins(0, 5, 0, 0)

        db_path = self.get_db_path_callback(self.media_config)
        stats = None
        if db_path and os.path.exists(db_path):
            db_util = DbScanUtil(db_path)
            stats = db_util.get_stats(self.media_config["path"])

        last_scanned_short, last_scanned_full = self._format_last_scanned(stats[7] if stats else None)

        # stats: (folder_path, subfolders, files, images, videos, nfo, other, last_scanned)
        stats_icons = [
            "fa6s.folder",
            "fa6s.file",
            "fa6s.image",
            "fa6s.film",
            "fa6s.info-circle",
            "fa6s.file-alt",
            "fa6s.clock"
        ]
        icon_tooltips = {
            "fa6s.folder": "Subfolders",
            "fa6s.file": "Files",
            "fa6s.image": "Images",
            "fa6s.film": "Videos",
            "fa6s.info-circle": "NFO Files",
            "fa6s.file-alt": "Other Files",
            "fa6s.clock": f"Last Scanned: {last_scanned_full}"
        }

        stats_data = [
            str(stats[1]) if stats else "-",
            str(stats[2]) if stats else "-",
            str(stats[3]) if stats else "-",
            str(stats[4]) if stats else "-",
            str(stats[5]) if stats else "-",
            str(stats[6]) if stats else "-",
            last_scanned_short
        ]

        for i, (icon_name, val) in enumerate(zip(stats_icons, stats_data)):
            pair_layout = QHBoxLayout()
            pair_layout.setContentsMargins(0, 0, 0, 0)
            pair_layout.setSpacing(1)
            pair_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            lbl = QLabel(val, parent=self)
            lbl.setObjectName(f"stats_val_{i}")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            # Keep counts compact while leaving room for longer timestamps.
            if icon_name == "fa6s.clock":
                lbl.setFixedWidth(110)
            elif icon_name == "fa6s.file":
                lbl.setFixedWidth(50)
            else:
                lbl.setFixedWidth(40)
            pair_layout.addWidget(lbl)

            icon_lbl = QLabel(parent=self)
            icon_lbl.setObjectName(f"stats_icon_{i}")
            icon_lbl.setPixmap(APP_THEME.icon(icon_name, color=APP_THEME.text_color).pixmap(16, 16))
            icon_lbl.setToolTip(icon_tooltips.get(icon_name, ""))
            if icon_name == "fa6s.clock":
                lbl.setToolTip(icon_tooltips.get(icon_name, ""))
                icon_lbl.setToolTip(icon_tooltips.get(icon_name, ""))
            pair_layout.addWidget(icon_lbl)

            self.stats_layout.addLayout(pair_layout)

            if i < len(stats_icons) - 1:
                self.stats_layout.addSpacing(5)

        self.stats_layout.addStretch()

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(True)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(APP_THEME.progress_bar_qss(active=False))

        self.scan_btn = QPushButton("Scan", parent=self)
        self.scan_btn.setStyleSheet(APP_THEME.button_qss())
        self.scan_btn.setFixedWidth(self.scan_btn.sizeHint().width() + 20)
        self.scan_btn.setEnabled(False)

        self.scan_btn.clicked.connect(
            lambda: self._start_scan(self.media_config, self.scan_btn, self.progress_bar)
        )
        self._refresh_scan_button_state()
        self.stats_layout.addWidget(self.scan_btn)

        layout.addLayout(self.stats_layout)
        layout.addWidget(self.progress_bar)

    def apply_theme(self) -> None:
        super().apply_theme()

        custom_qss = APP_THEME.settings_media_folder_browser_section_qss()
        if custom_qss not in self.styleSheet():
             self.setStyleSheet(self.styleSheet() + custom_qss)

    @staticmethod
    def _safe_db_label(label: str) -> str:
        text = str(label).strip()
        if not text:
            return ""
        text = re.sub(r"[\\/:*?\"<>|]", "_", text)
        text = re.sub(r"[^a-zA-Z0-9_.\-\s]", "_", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = text.strip(" ._-")
        return text

    def _rename_db_file_if_needed(self, media_config: dict[str, Any]) -> None:
        previous_label = str(media_config.get("_previous_label", "")).strip()
        current_label = str(media_config.get("label", "")).strip()
        if not previous_label or previous_label == current_label:
            media_config["_previous_label"] = current_label
            return

        previous_db = f"db/{self._safe_db_label(previous_label)}.db"
        current_db = f"db/{self._safe_db_label(current_label)}.db"

        if previous_db == current_db:
            media_config["_previous_label"] = current_label
            return

        if os.path.exists(current_db) and not os.path.exists(previous_db):
            raise ValueError(
                f"The database file '{os.path.basename(current_db)}' already exists. "
                "Choose a unique media name."
            )

        if os.path.exists(previous_db):
            try:
                os.replace(previous_db, current_db)
            except OSError as exc:
                raise OSError(
                    f"Unable to rename database file from '{os.path.basename(previous_db)}' to '{os.path.basename(current_db)}'. "
                    f"Original media name kept. Details: {exc}"
                ) from exc

        media_config["_previous_label"] = current_label

    def _refresh_scan_button_state(self) -> None:
        if not hasattr(self, "scan_btn"):
            return

        label = self.label_edit.text().strip()
        path = self.folder_edit.text().strip()
        worker = getattr(self, "worker", None)
        is_running = worker is not None and worker.isRunning()
        self.scan_btn.setEnabled(bool(label) and bool(path) and not is_running)

    def apply_changes(self) -> None:
        previous_label = str(self.media_config.get("label", "")).strip()
        new_label = self.label_edit.text().strip()
        if new_label != previous_label:
            self.media_config["_previous_label"] = previous_label

        self.media_config["label"] = new_label
        self.media_config["media_type"] = self.type_combo.currentData()
        self.media_config["icon"] = self.icon_combo.currentData()
        self.media_config["path"] = self.folder_edit.text()
        self.config_changed.emit(self.media_config, "label", self.media_config["label"])
        self.config_changed.emit(self.media_config, "media_type", self.media_config["media_type"])
        self.config_changed.emit(self.media_config, "icon", self.media_config["icon"])
        self.config_changed.emit(self.media_config, "path", self.media_config["path"])
        self._refresh_scan_button_state()

    @staticmethod
    def _format_scan_error(error: BaseException, media_config: dict[str, Any]) -> str:
        label = str(media_config.get("label", "")).strip()
        folder = str(media_config.get("path", "")).strip()

        if not label:
            return "Please enter a media name before scanning."
        if not folder:
            return "Please choose a media folder before scanning."

        if "media name is empty or contains no valid characters for database storage" in str(error).lower():
            return (
                f"The media name '{label}' is not valid for database storage. "
                "Use letters, numbers, spaces, dashes, or underscores and try again."
            )

        details = str(error).strip()
        if not details:
            details = "The database could not be written to disk."
        return (
            "The scan could not be saved to the database. "
            f"Please check the media name, folder path, and database permissions.\n\n{details}"
        )

    @staticmethod
    def _format_progress_error_text(message: str, max_len: int = 90) -> str:
        text = str(message).replace("\n", " ").strip()
        if len(text) > max_len:
            text = text[: max_len - 3].rstrip() + "..."
        return text

    def _show_scan_error(
        self,
        error: BaseException,
        media_config: dict[str, Any],
        progress_bar: QProgressBar | None = None,
    ) -> None:
        message = self._format_scan_error(error, media_config)
        if progress_bar is not None:
            self._scan_error = True
            progress_bar.setRange(0, 100)
            progress_bar.setValue(100)
            progress_bar.setTextVisible(True)
            progress_bar.setFormat(f"Error: {self._format_progress_error_text(message)}")
            progress_bar.setStyleSheet(
                "QProgressBar { color: #f5d0d0; background: #2f1f1f; border: 1px solid #8b3b3b; } "
                "QProgressBar::chunk { background: #b3261e; }"
            )

    @staticmethod
    def _format_last_scanned(value: Any) -> tuple[str, str]:
        if not value:
            return "n/a", "n/a"
        try:
            return value.strftime("%m/%d %I%p").lower(), value.strftime("%Y-%m-%d %I:%M%p").lower()
        except AttributeError:
            return "n/a", "n/a"

    def _refresh_stats_labels(self, media_config: dict[str, Any]) -> None:
        db_path = self.get_db_path_callback(media_config)
        stats = None
        if os.path.exists(db_path):
            db_util = DbScanUtil(db_path)
            stats = db_util.get_stats(media_config["path"])

        last_scanned_short, last_scanned_full = self._format_last_scanned(stats[7] if stats else None)
        stats_data = [
            str(stats[1]) if stats else "-",
            str(stats[2]) if stats else "-",
            str(stats[3]) if stats else "-",
            str(stats[4]) if stats else "-",
            str(stats[5]) if stats else "-",
            str(stats[6]) if stats else "-",
            last_scanned_short,
        ]

        for i, val in enumerate(stats_data):
            lbl = self.findChild(QLabel, f"stats_val_{i}")
            if lbl:
                lbl.setText(val)
                if i == 6:
                    lbl.setToolTip(f"Last Scanned: {last_scanned_full}")

            icon_lbl = self.findChild(QLabel, f"stats_icon_{i}")
            if icon_lbl and i == 6:
                icon_lbl.setToolTip(f"Last Scanned: {last_scanned_full}")

    def _start_scan(
        self,
        media_config: dict[str, Any],
        scan_btn: QPushButton,
        progress_bar: QProgressBar,
    ) -> None:
        self.apply_changes()
        label = str(media_config.get("label", "")).strip()
        folder = str(media_config.get("path", "")).strip()
        if not label or not folder:
            QMessageBox.warning(
                self,
                "Scan required",
                "Please enter both a media name and a media folder before scanning.",
            )
            self._refresh_scan_button_state()
            return

        try:
            self._rename_db_file_if_needed(media_config)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(
                self,
                "Invalid Media Name",
                str(exc),
            )
            return

        self._scan_error = False
        scan_btn.setEnabled(False)
        scan_btn.setText("Scan")

        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setFormat(f"{self.lang.scan_progress['scanning_media_subfolders']} 0%")
        progress_bar.setTextVisible(True)
        progress_bar.setStyleSheet(APP_THEME.progress_bar_qss(active=True))

        self.worker = ScanWorker(media_config, self.file_util, self.nfo_util)
        self.worker.progress_init.connect(lambda _val: progress_bar.setRange(0, 100))
        self.worker.progress_updated.connect(progress_bar.setValue)
        stage_state = {"stage": self.lang.scan_progress["scanning_media_subfolders"]}
        self.worker.progress_stage.connect(lambda stage: stage_state.__setitem__("stage", stage))
        self.worker.progress_updated.connect(
            lambda val: progress_bar.setFormat(f"{stage_state['stage']} {val}%")
        )
        self.worker.error.connect(
            lambda message: self._show_scan_error(RuntimeError(message), media_config, progress_bar)
        )
        self.worker.finished.connect(
            lambda: self._on_scan_finished(scan_btn, progress_bar, media_config)
        )
        self.worker.start()

    def _on_scan_finished(self, scan_btn: QPushButton, progress_bar: QProgressBar, media_config: dict[str, Any]) -> None:
        if getattr(self, "_scan_error", False):
            self._refresh_scan_button_state()
            return

        progress_bar.setValue(100)
        progress_bar.setRange(0, 100)
        progress_bar.setFormat(f"{self.lang.scan_progress['done']} 100%")
        progress_bar.setTextVisible(False)
        progress_bar.setStyleSheet(APP_THEME.progress_bar_qss(active=False))
        scan_btn.setText("Scan")
        self._refresh_scan_button_state()

        self._refresh_stats_labels(media_config)

    def _on_folder_selected(self, path: str) -> None:
        self.folder_edit.setText(path)
