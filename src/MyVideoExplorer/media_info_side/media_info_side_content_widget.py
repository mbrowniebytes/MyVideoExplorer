from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from MyVideoExplorer.media_info_side.media_info_side_facts_widget import MediaInfoSideFactsWidget
from MyVideoExplorer.media_info_side.media_info_side_header_widget import MediaInfoSideHeaderWidget
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.str_util import StrUtil


class MediaInfoSideContentWidget(QWidget, ThemableMixin):
    """Reusable framed side panel content for media metadata and quick actions."""

    sig_play_video_requested = Signal(object)

    def __init__(
        self,
        str_util: StrUtil,
        log_util: LogUtil | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.log_util = log_util or LogUtil()

        self.setObjectName("side_media_info")

        self.header_widget = MediaInfoSideHeaderWidget()
        self.facts_widget = MediaInfoSideFactsWidget(str_util)

        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addWidget(self.header_widget)
        self.content_layout.addWidget(self.facts_widget)

        self.header_widget.sig_play_video_requested.connect(
            lambda p: self.sig_play_video_requested.emit(p)
        )

        self.apply_theme()

    def update_from_movie_info(self, movie_info: dict) -> None:
        self.facts_widget.update_from_movie_info(movie_info)

    def apply_theme(self) -> None:
        if not APP_THEME.is_refreshing:
            super().apply_theme()
            return

        self.setStyleSheet(APP_THEME.container_qss())
        self.header_widget.apply_theme()
        self.facts_widget.apply_theme()
