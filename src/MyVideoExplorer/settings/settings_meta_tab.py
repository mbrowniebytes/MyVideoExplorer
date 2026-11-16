from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.db.models.ffprobe_stats import FfprobeStats
from MyVideoExplorer.lang.lang_en import LangEn
from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.ffprobe_util import FfprobeUtil
from MyVideoExplorer.utils.ffprobe_worker import FfprobeWorker
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.buttons.action_button import ActionButton
from MyVideoExplorer.widgets.combo_boxes.select_combo_box import SelectComboBox

logger = logging.getLogger(__name__)


class SettingsMetaTab(SettingsBaseTab):
    """Settings sub-tab for ffmpeg-based media metadata scanning configuration."""

    scan_requested = Signal(object)

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
        self._current_worker: FfprobeWorker | None = None
        self._scan_index = 0
        self._scan_configs: list[dict[str, str]] = []
        self._scan_new_only = False
        self._ffmpeg_folder = ""
        self._meta_stats_by_label: dict[str, FfprobeStats | None] = {}

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

        self._build_ui()

        scroll.setWidget(self.main_widget)
        self._layout.addWidget(scroll)

    # ---- UI Construction ----

    def _build_ui(self) -> None:
        # ffmpeg label
        ffmpeg_label = QLabel(self.lang.ui.settings.meta.ffmpeg_label, parent=self)
        ffmpeg_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 1))
        ffmpeg_label.setStyleSheet(APP_THEME.label_qss("secondary"))
        self.content_layout.addWidget(ffmpeg_label)

        # Download link
        self.ffmpeg_download_link = QLabel(
            f'<a href="https://ffmpeg.org/download.html">{self.lang.ui.settings.meta.download_link}</a>',
            parent=self,
        )
        self.ffmpeg_download_link.setTextFormat(Qt.TextFormat.RichText)
        self.ffmpeg_download_link.setOpenExternalLinks(True)
        self.ffmpeg_download_link.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        self.ffmpeg_download_link.setStyleSheet(
            "color: #58A6FF; text-decoration: underline;"
        )
        self.ffmpeg_download_link.linkActivated.connect(self._on_download_link_clicked)
        self.content_layout.addWidget(self.ffmpeg_download_link)

        # ffmpeg path picker
        path_layout = QHBoxLayout()
        path_layout.setSpacing(5)

        self.ffmpeg_path_edit = QLineEdit(parent=self)
        self.ffmpeg_path_edit.setPlaceholderText(self.lang.ui.settings.meta.placeholder)
        self.ffmpeg_path_edit.textChanged.connect(self._on_ffmpeg_path_changed)
        path_layout.addWidget(self.ffmpeg_path_edit)

        browse_btn = QPushButton(self.lang.ui.settings.meta.browse, parent=self)
        browse_btn.clicked.connect(self._on_browse_ffmpeg)
        path_layout.addWidget(browse_btn)

        self.content_layout.addLayout(path_layout)

        # ffmpeg status label
        self.ffmpeg_status_label = QLabel(parent=self)
        self.ffmpeg_status_label.hide()
        self.content_layout.addWidget(self.ffmpeg_status_label)

        # Scan target dropdown
        target_layout = QHBoxLayout()
        target_layout.setSpacing(5)
        target_label = QLabel(self.lang.ui.settings.meta.scan_target, parent=self)
        target_layout.addWidget(target_label)

        self.scan_target_combo = SelectComboBox(self)
        self._populate_scan_targets()
        target_layout.addWidget(self.scan_target_combo, 1)
        target_layout.addStretch()

        self.content_layout.addLayout(target_layout)

        # Scan mode checkbox
        self.scan_new_checkbox = QCheckBox(
            self.lang.ui.settings.meta.scan_new, parent=self
        )
        self.content_layout.addWidget(self.scan_new_checkbox)

        # Scan button + Stop button
        scan_btn_layout = QHBoxLayout()
        self.scan_button = ActionButton(
            self,
            icon_name="fa6s.magnifying-glass",
            tooltip=self.lang.ui.settings.meta.scan_tooltip,
            text=self.lang.ui.settings.meta.scan,
        )
        self.scan_button.clicked.connect(self._on_scan_clicked)
        self.scan_button.setEnabled(False)
        scan_btn_layout.addWidget(self.scan_button)

        self.stop_button = ActionButton(
            self,
            icon_name="fa6s.stop",
            tooltip=self.lang.ui.settings.meta.stop_tooltip,
            text=self.lang.ui.settings.meta.stop,
        )
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.stop_button.hide()
        scan_btn_layout.addWidget(self.stop_button)

        self.scan_stats_layout = QHBoxLayout()
        self.scan_stats_layout.setContentsMargins(0, 0, 0, 0)
        scan_btn_layout.addLayout(self.scan_stats_layout, 1)
        self.content_layout.addLayout(scan_btn_layout)
        self.scan_target_combo.currentTextChanged.connect(self._refresh_scan_stats)

        # Folder progress label (e.g., "Scanning M1a (1 of 4)")
        self.folder_progress_label = QLabel(parent=self)
        self.folder_progress_label.hide()
        self.folder_progress_label.setStyleSheet(APP_THEME.label_qss("secondary"))
        self.content_layout.addWidget(self.folder_progress_label)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.hide()
        self.progress_bar.setRange(0, 0)
        self.content_layout.addWidget(self.progress_bar)

        # Stage label (shows current file / status)
        self.stage_label = QLabel(parent=self)
        self.stage_label.hide()
        self.stage_label.setStyleSheet(APP_THEME.label_qss("secondary"))
        self.content_layout.addWidget(self.stage_label)

        self.content_layout.addStretch()

        # Save/Reset buttons
        save_btn_container = QWidget(self)
        save_btn_container.setObjectName("meta_settings_footer")
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.reset_btn = self._build_reset_button(
            self.lang.ui.settings.meta.reset_btn, self.reset_settings
        )

        self.save_btn = QPushButton(self.lang.ui.settings.meta.save_btn, parent=self)
        self.save_btn.clicked.connect(self._save_meta_settings)

        save_btn_layout.addWidget(self.reset_btn)
        save_btn_layout.addStretch()
        save_btn_layout.addWidget(self.save_btn)

        self.content_layout.addWidget(
            save_btn_container,
            alignment=Qt.AlignmentFlag.AlignBottom,
        )

        # Initialize from state
        self._load_from_state()

    # ---- Actions ----

    def _on_download_link_clicked(self, url: str) -> None:
        QDesktopServices.openUrl(QUrl(url))

    def _on_browse_ffmpeg(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, self.lang.ui.settings.meta.browse_title
        )
        if folder:
            normalized = self.file_util.normalize_path(folder)
            self.ffmpeg_path_edit.setText(normalized)

    def _on_ffmpeg_path_changed(self, text: str) -> None:
        self._validate_ffmpeg_path()
        self._on_setting_changed()

    def _on_scan_clicked(self) -> None:
        target = self.scan_target_combo.currentText()
        scan_new_only = self.scan_new_checkbox.isChecked()
        ffmpeg_folder = self.ffmpeg_path_edit.text().strip()

        if not ffmpeg_folder or not self._is_ffmpeg_valid():
            return

        # Determine which media configs to scan
        if target == self.lang.ui.settings.meta.scan_all:
            configs = list(self.state.media_configs)
        else:
            configs = [c for c in self.state.media_configs if c.get("label") == target]

        if not configs:
            return

        # UI: show progress, hide scan, show stop
        self.scan_button.setEnabled(False)
        self.scan_button.hide()
        self.stop_button.show()
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)
        self.folder_progress_label.show()
        self.stage_label.show()
        self.stage_label.setText(self.lang.ui.settings.meta.starting_scan)

        # Emit signal for external listeners
        payload = SignalPayload(
            data={
                "ffmpeg_path": ffmpeg_folder,
                "target": "all"
                if target == self.lang.ui.settings.meta.scan_all
                else target,
                "scan_new_only": scan_new_only,
            },
            sender=self.__class__.__name__,
            name="Scan Requested",
            description="User requested an ffmpeg-based media scan.",
            flow=SignalFlow.USER_INPUT,
        )
        self.scan_requested.emit(payload)

        # Start scanning sequentially
        self._scan_index = 0
        self._scan_configs = configs
        self._scan_new_only = scan_new_only
        self._ffmpeg_folder = ffmpeg_folder
        self._start_next_scan()

    def _start_next_scan(self) -> None:
        try:
            if self._scan_index >= len(self._scan_configs):
                self._on_all_scans_finished()
                return

            config = self._scan_configs[self._scan_index]
            config_label = str(config.get("label", "Unnamed"))
            total_configs = len(self._scan_configs)
            current_index = self._scan_index + 1

            self.folder_progress_label.setText(
                self.lang.ui.settings.meta.scanning.format(
                    label=config_label, current=current_index, total=total_configs
                )
            )

            worker = FfprobeWorker(
                ffmpeg_folder=self._ffmpeg_folder,
                media_config=config,
                scan_new_only=self._scan_new_only,
                file_util=self.file_util,
                parent=self,
            )
            self._current_worker = worker

            worker.progress_init.connect(self._on_worker_progress_init)
            worker.progress_updated.connect(self._on_worker_progress_updated)
            worker.progress_stage.connect(self._on_worker_stage)
            worker.stats_updated.connect(self._on_worker_stats_updated)
            worker.error.connect(self._on_worker_error)
            worker.finished.connect(self._on_worker_finished)

            worker.start()
        except Exception:
            logger.exception("Error starting ffprobe worker")
            self._on_scan_finished()

    def _on_worker_progress_init(self, total: int) -> None:
        try:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(0)
        except Exception as exc:
            logger.error("Error in progress_init handler: %s", exc)

    def _on_worker_progress_updated(self, current: int, file_name: str) -> None:
        try:
            self.progress_bar.setValue(current)
            self.stage_label.setText(
                self.lang.ui.settings.meta.progress.format(
                    current=current, total=self.progress_bar.maximum(), file=file_name
                )
            )
        except Exception as exc:
            logger.error("Error in progress_updated handler: %s", exc)

    def _on_worker_stage(self, stage: str) -> None:
        try:
            self.stage_label.setText(stage)
        except Exception as exc:
            logger.error("Error in stage handler: %s", exc)

    def _on_worker_error(self, message: str) -> None:
        try:
            self.stage_label.setText(
                self.lang.ui.settings.meta.error.format(message=message)
            )
        except Exception as exc:
            logger.error("Error in error handler: %s", exc)

    def _on_worker_finished(self) -> None:
        try:
            # Clean up the finished worker
            if self._current_worker is not None:
                self._current_worker.deleteLater()
                self._current_worker = None

            self._refresh_scan_stats()
            self._scan_index += 1
            if self._scan_index >= len(self._scan_configs):
                self._on_scan_finished()
            else:
                self._start_next_scan()
        except Exception:
            logger.exception("Error in worker finished handler")
            self._on_scan_finished()

    def _on_all_scans_finished(self) -> None:
        self._on_scan_finished()

    def _on_scan_finished(self) -> None:
        self.progress_bar.hide()
        self.folder_progress_label.hide()
        self.stage_label.hide()
        self.stop_button.hide()
        self.scan_button.show()
        self.scan_button.setEnabled(self._is_ffmpeg_valid())

    def _on_stop_clicked(self) -> None:
        if hasattr(self, "_current_worker") and self._current_worker is not None:
            logger.info("Stop button clicked — requesting interruption")
            self._current_worker.requestInterruption()
            self.stage_label.setText(self.lang.ui.settings.meta.cancelling)

    # ---- Validation ----

    def _find_ffmpeg_binary(self, folder_path: str) -> Path | None:
        """Check for the ffmpeg binary in the given folder.

        On Windows, looks for `ffmpeg.exe`. On macOS/Linux, looks for `ffmpeg`.
        """
        folder = Path(folder_path)
        if not folder.is_dir():
            return None

        binary_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        binary_path = folder / binary_name
        return binary_path if binary_path.is_file() else None

    def _validate_ffmpeg_path(self) -> bool:
        """Validate the current ffmpeg path and update UI accordingly."""
        path_text = self.ffmpeg_path_edit.text().strip()

        if not path_text:
            self.ffmpeg_status_label.hide()
            self.scan_button.setEnabled(False)
            return False

        binary = self._find_ffmpeg_binary(path_text)
        if binary is not None:
            self.ffmpeg_status_label.setText(self.lang.ui.settings.meta.ffmpeg_found)
            self.ffmpeg_status_label.setStyleSheet("color: #3FB950;")
            self.ffmpeg_status_label.show()
            self.scan_button.setEnabled(True)
            return True
        self.ffmpeg_status_label.setText(self.lang.ui.settings.meta.ffmpeg_not_found)
        self.ffmpeg_status_label.setStyleSheet("color: #F85149;")
        self.ffmpeg_status_label.show()
        self.scan_button.setEnabled(False)
        return False

    def _is_ffmpeg_valid(self) -> bool:
        path_text = self.ffmpeg_path_edit.text().strip()
        if not path_text:
            return False
        return self._find_ffmpeg_binary(path_text) is not None

    # ---- Data binding ----

    def _populate_scan_targets(self) -> None:
        self.scan_target_combo.clear()
        self.scan_target_combo.addItem(self.lang.ui.settings.meta.scan_all)
        for config in self.state.media_configs:
            label = config.get("label", "Unnamed")
            if label:
                self.scan_target_combo.addItem(label)

    def _format_last_probed(self, value: datetime | None) -> str:
        if not value:
            return self.lang.ui.settings.meta.na
        try:
            return value.strftime("%Y-%m-%d %I:%M%p").lower()
        except AttributeError:
            return self.lang.ui.settings.meta.na

    def _get_stats(self, config: dict[str, Any]) -> FfprobeStats | None:
        db_path = self.state.get_db_path(config)
        if not Path(db_path).is_file():
            return None
        return FfprobeUtil(self.ffmpeg_path_edit.text().strip(), db_path).get_stats()

    def _clear_stats_layout(self) -> None:
        """Remove all widgets from the stats layout."""
        while self.scan_stats_layout.count():
            item = self.scan_stats_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.deleteLater()
            else:
                nested = item.layout()
                if nested is not None:
                    # Recursively clear nested layout items
                    while nested.count():
                        nested_item = nested.takeAt(0)
                        if nested_item is None:
                            continue
                        nw = nested_item.widget()
                        if nw is not None:
                            nw.deleteLater()
                        else:
                            nlayout = nested_item.layout()
                            if nlayout is not None:
                                nlayout.deleteLater()
                    nested.deleteLater()

    def _refresh_scan_stats(self, _target: str | None = None) -> None:
        target = self.scan_target_combo.currentText()
        if target == self.lang.ui.settings.meta.scan_all:
            configs = list(self.state.media_configs)
        else:
            configs = [
                config
                for config in self.state.media_configs
                if config.get("label") == target
            ]

        if not configs:
            self._clear_stats_layout()
            self.scan_stats_layout.addStretch()
            return

        try:
            for config in configs:
                label = str(config.get("label", ""))
                self._meta_stats_by_label[label] = self._get_stats(config)
        except Exception as exc:
            logger.exception("Failed to load Meta scan statistics")
            self._clear_stats_layout()
            err_label = QLabel(
                self.lang.ui.settings.meta.unable_to_load_stats.format(error=exc),
                parent=self,
            )
            err_label.setStyleSheet(APP_THEME.label_qss("secondary"))
            self.scan_stats_layout.addWidget(err_label)
            return

        self._display_scan_stats(configs)

    def _on_worker_stats_updated(self, label: str, stats: FfprobeStats) -> None:
        self._meta_stats_by_label[label] = stats
        self._display_scan_stats(self._get_display_configs())

    def _get_display_configs(self) -> list[dict[str, str]]:
        target = self.scan_target_combo.currentText()
        if target == self.lang.ui.settings.meta.scan_all:
            return list(self.state.media_configs)
        return [
            config
            for config in self.state.media_configs
            if config.get("label") == target
        ]

    def _display_scan_stats(self, configs: list[dict[str, str]]) -> None:
        self._clear_stats_layout()

        available = [
            self._meta_stats_by_label.get(str(config.get("label", "")))
            for config in configs
        ]
        available = [item for item in available if item is not None]

        if not available:
            self.scan_stats_layout.addStretch()
            return

        totals = {
            "fa6s.database": sum(item.probed_files for item in available),
            "fa6s.video": sum(item.video_streams for item in available),
            "fa6s.music": sum(item.audio_streams for item in available),
            "fa6s.closed-captioning": sum(item.subtitle_streams for item in available),
        }
        latest_scan = max(
            (item.last_probed for item in available if item.last_probed),
            default=None,
        )
        totals["fa6s.clock"] = self._format_last_probed(latest_scan)

        icon_tooltips = {
            "fa6s.database": self.lang.ui.settings.meta.probed_files,
            "fa6s.video": self.lang.ui.settings.meta.video_streams,
            "fa6s.music": self.lang.ui.settings.meta.audio_streams,
            "fa6s.closed-captioning": self.lang.ui.settings.meta.subtitle_streams,
            "fa6s.clock": self.lang.ui.settings.meta.last_probed.format(
                date=self._format_last_probed(latest_scan)
            ),
        }

        for i, (icon_name, count) in enumerate(totals.items()):
            pair_layout = QHBoxLayout()
            pair_layout.setContentsMargins(0, 0, 0, 0)
            pair_layout.setSpacing(1)
            pair_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            val_str = f"{count:,}" if isinstance(count, int) else str(count)
            lbl = QLabel(val_str, parent=self)
            lbl.setObjectName(f"meta_stats_val_{i}")
            lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            lbl.setStyleSheet(APP_THEME.label_qss("secondary"))
            if icon_name == "fa6s.clock":
                lbl.setFixedWidth(110)
            else:
                lbl.setFixedWidth(50)
            pair_layout.addWidget(lbl)

            icon_lbl = QLabel(parent=self)
            icon_lbl.setObjectName(f"meta_stats_icon_{i}")
            icon_lbl.setPixmap(
                APP_THEME.icon(icon_name, color=APP_THEME.text_color).pixmap(16, 16)
            )
            icon_lbl.setToolTip(icon_tooltips.get(icon_name, ""))
            if icon_name == "fa6s.clock":
                lbl.setToolTip(icon_tooltips.get(icon_name, ""))
            pair_layout.addWidget(icon_lbl)

            self.scan_stats_layout.addLayout(pair_layout)

            if i < len(totals) - 1:
                self.scan_stats_layout.addSpacing(8)

        if len(available) < len(configs):
            partial_label = QLabel(
                self.lang.ui.settings.meta.partial_metadata.format(
                    available=len(available), total=len(configs)
                ),
                parent=self,
            )
            partial_label.setStyleSheet(APP_THEME.label_qss("secondary"))
            self.scan_stats_layout.addWidget(partial_label)

        self.scan_stats_layout.addStretch()

    def _load_from_state(self) -> None:
        # Block signals while loading to avoid marking the tab as dirty
        self.ffmpeg_path_edit.blockSignals(True)
        try:
            self.ffmpeg_path_edit.setText(self.state.ffmpeg_path)
            self._validate_ffmpeg_path()
        finally:
            self.ffmpeg_path_edit.blockSignals(False)
        self._populate_scan_targets()
        self._refresh_scan_stats()

    # ---- Persistence ----

    def _save_meta_settings(self) -> None:
        self.state.ffmpeg_path = self.ffmpeg_path_edit.text().strip()
        self.state.save_media()
        self.reset_save_button()
        self.saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Meta Settings Saved",
                description="Meta settings were saved.",
                flow=SignalFlow.USER_INPUT,
            )
        )

    def reset_settings(self) -> None:
        """Reset Meta settings to defaults."""
        self.state.load_media()
        self._load_from_state()
        self.reset_save_button()
        self.saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Meta Settings Reset",
                description="Meta settings were reset to defaults.",
                flow=SignalFlow.USER_INPUT,
            )
        )

    # ---- Theme ----

    def apply_theme(self) -> None:
        super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.setFont(font)
        self.ffmpeg_download_link.setStyleSheet(
            "color: #58A6FF; text-decoration: underline;"
        )

    # ---- Lifecycle ----

    def refresh_scan_targets(self) -> None:
        """Repopulate the scan target dropdown when media configs change."""
        self._populate_scan_targets()
        self._refresh_scan_stats()
