from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

from src.media_info.media_info_side_view import MediaInfoSideView
from src.media_info.media_info_view import MediaInfoView
from src.utils.nfo_parse_util import NfoParseUtil


from src.widgets.base_widget import BaseWidget


class MediaInfo(BaseWidget):
    sig_play_video = Signal(str)

    def __init__(
        self,
        media_info_view: MediaInfoView,
        media_info_side_view: MediaInfoSideView,
        nfo_parse_util: NfoParseUtil,
        log_util,
    ) -> None:
        super().__init__(log_util)
        self.media_info_side_view = media_info_side_view
        self.media_info_view = media_info_view
        self.nfo_parse_util = nfo_parse_util
        self.folder_path: str = ""
        self.image_path: str = ""
        self.media_info = QWidget()
        self.media_info_layout = QVBoxLayout(self.media_info)
        self._signals_connected = False

    def _connect_internal_sigs(self) -> None:
        if self._signals_connected:
            return
        print("_connect_internal_sigs")
        self.media_info_view.sig_info_play_video_btn_clicked.connect(
            self._emit_play_request
        )
        self.media_info_side_view.sig_info_side_play_video_btn_clicked.connect(
            self._emit_play_request
        )
        self._signals_connected = True

    def build(self):
        self.media_info_layout.addWidget(self.media_info_view)
        self._connect_internal_sigs()
        return self.media_info

    def set_image_path(self, image_path: str) -> None:
        print(f"set_image_path: {image_path}")
        self.image_path = image_path

    def refresh(
        self,
        folder_path: str,
        tab_index: int,
        image_path: str = "",
    ) -> None:
        if (
            self.folder_path == folder_path
            and self.media_info.property("tab_index") == tab_index
        ):
            return

        self.folder_path = folder_path
        self.media_info.setProperty("tab_index", tab_index)

        self.media_info_view.refresh(folder_path=folder_path)
        self.media_info_side_view.refresh(folder_path=folder_path)

    def _emit_play_request(self) -> None:
        print(f"_emit_play_request: {self.image_path} {self.folder_path}")
        self.sig_play_video.emit(self.image_path)
        self.log_util.debug(f"sig_play_video emitted with: {self.image_path}")

    def apply_theme(self) -> None:
        if self.media_info_view is not None:
            self.media_info_view.apply_theme()
        if self.media_info_side_view is not None:
            self.media_info_side_view.apply_theme()
