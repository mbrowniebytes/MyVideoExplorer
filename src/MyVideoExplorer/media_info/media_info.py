from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.media_info.media_info_view import MediaInfoView
from MyVideoExplorer.media_info_side.media_info_side_view import MediaInfoSideView
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.ui_utils import UIUtils


class MediaInfo(QWidget, ThemableMixin):
    sig_play_video = Signal(object)

    def __init__(
        self,
        media_info_view: MediaInfoView,
        media_info_side_view: MediaInfoSideView,
        log_util: LogUtil,
    ) -> None:
        super().__init__()
        self.log_util = log_util
        self._ui_utils = UIUtils()

        self.media_info_view = media_info_view
        self.media_info_side_view = media_info_side_view

        self.current_folder_path: str = ""
        self.current_image_path: str = ""
        self.current_tab_index: int | None = None
        self._are_child_signals_connected = False

        self.media_info_layout = self._ui_utils.apply_compact_layout(self, QVBoxLayout)

        # Backward-compatible aliases for existing tests/callers.
        self.folder_path = self.current_folder_path
        self.image_path = self.current_image_path
        self.media_info: QWidget = self

    def build(self) -> QWidget:
        if self.media_info_layout.indexOf(self.media_info_view) == -1:
            self.media_info_layout.addWidget(self.media_info_view)

        self._connect_child_signals()
        return self

    def refresh(
        self,
        folder_path: str,
        tab_index: int,
        image_path: str = "",
    ) -> None:
        if image_path:
            self.set_image_path(image_path)

        if self._is_current_selection(folder_path=folder_path, tab_index=tab_index):
            return

        self.current_folder_path = folder_path
        self.current_tab_index = tab_index

        # Backward-compatible alias.
        self.folder_path = self.current_folder_path

        self.media_info_view.refresh(folder_path=folder_path)
        self.media_info_side_view.refresh(folder_path=folder_path)

    def set_image_path(self, image_path: str) -> None:
        self.current_image_path = image_path

        # Backward-compatible alias.
        self.image_path = self.current_image_path

        if self.log_util:
            self.log_util.debug(
                f"MediaInfo image path set to: {self.current_image_path}"
            )

    def apply_theme(self) -> None:
        if not APP_THEME.is_refreshing:
            super().apply_theme()
            return

        self.media_info_view.apply_theme()
        self.media_info_side_view.apply_theme()

    def _connect_child_signals(self) -> None:
        if self._are_child_signals_connected:
            return

        self.media_info_view.sig_info_play_video_btn_clicked.connect(
            self._emit_play_video_requested
        )
        self.media_info_side_view.sig_info_side_play_video_btn_clicked.connect(
            self._emit_play_video_requested
        )
        self._are_child_signals_connected = True

    def _is_current_selection(self, folder_path: str, tab_index: int) -> bool:
        return (
            self.current_folder_path == folder_path
            and self.current_tab_index == tab_index
        )

    def _emit_play_video_requested(self, payload: SignalPayload = None) -> None:
        self.sig_play_video.emit(
            SignalPayload(
                data=self.current_image_path,
                sender=self.__class__.__name__,
                name="Play Video Requested",
                description="Emitted when play video is requested from child views.",
                flow=SignalFlow.USER_INPUT,
            )
        )

        self.log_util.debug(
            f"MediaInfo play video requested for image path: {self.current_image_path}"
        )
