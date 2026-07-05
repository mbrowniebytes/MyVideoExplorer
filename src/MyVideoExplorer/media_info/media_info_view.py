from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.media_info.media_info_scroll_content_widget import (
    MediaInfoScrollContentWidget,
)
from MyVideoExplorer.media_info.media_info_toolbar_widget import MediaInfoToolbarWidget
from MyVideoExplorer.media_info_section.media_info_section_actors import (
    MediaInfoActorsSection,
)
from MyVideoExplorer.media_info_section.media_info_section_common import (
    MediaInfoCommonSection,
)
from MyVideoExplorer.media_info_section.media_info_section_definitions import (
    MEDIA_INFO_SECTION_ACTORS,
    MEDIA_INFO_SECTION_AUDIOS,
    MEDIA_INFO_SECTION_COMMON,
    MEDIA_INFO_SECTION_IDS,
    MEDIA_INFO_SECTION_PLOT,
    MEDIA_INFO_SECTION_SUBTITLES,
    MEDIA_INFO_SECTION_VIDEOS,
    MEDIA_INFO_SECTIONS_HIDDEN_IN_IMAGE_LIST,
    MEDIA_INFO_VIEW_MODE_DEFAULT,
    MEDIA_INFO_VIEW_MODE_IMAGE_LIST,
)
from MyVideoExplorer.media_info_section.media_info_section_details import (
    MediaInfoDetailsSection,
)
from MyVideoExplorer.media_info_section.media_info_section_plot import (
    MediaInfoPlotSection,
)
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.utils.str_util import StrUtil
from MyVideoExplorer.utils.ui_utils import UIUtils


class MediaInfoView(QWidget, ThemableMixin):
    sig_info_play_video_btn_clicked = Signal(object)

    def __init__(
        self,
        nfo_parse_util: NfoParseUtil,
        str_util: StrUtil,
        log_util: LogUtil,
    ) -> None:
        super().__init__()
        self.log_util = log_util
        self._ui_utils = UIUtils()

        self.nfo_parse_util = nfo_parse_util
        self.str_util = str_util

        self.movie_info: dict = {}
        self.view_mode = MEDIA_INFO_VIEW_MODE_DEFAULT

        self.toolbar_widget = MediaInfoToolbarWidget()
        self.scroll_content_widget = MediaInfoScrollContentWidget(log_util)

        self.common_section = MediaInfoCommonSection(self.str_util)
        self.plot_section = MediaInfoPlotSection()
        self.ids_section = MediaInfoDetailsSection()
        self.videos_section = MediaInfoDetailsSection()
        self.audios_section = MediaInfoDetailsSection()
        self.subtitles_section = MediaInfoDetailsSection()
        self.actors_section = MediaInfoActorsSection()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.toolbar_widget)
        self.main_layout.addWidget(self.scroll_content_widget)

        self.toolbar_widget.sig_section_visibility_toggle_requested.connect(
            lambda p: self._toggle_section(p.data)
        )
        self.toolbar_widget.sig_play_video_requested.connect(self.play_video)

        # Backward-compatible aliases for existing tests/callers.
        self.section_widgets = self.scroll_content_widget.section_widgets_by_id
        self.toggle_layout = self.toolbar_widget.toolbar_layout
        self.content_container = self.scroll_content_widget.content_container_widget
        self.media_info_layout = self.scroll_content_widget.section_layout
        self.scroll_area = self.scroll_content_widget.scroll_area

    def refresh(self, folder_path: str) -> None:
        parsed_movie_info = self.nfo_parse_util.parse_nfo(folder_path=folder_path)
        self.set_movie_info(parsed_movie_info)

    def set_movie_info(self, movie_info: dict) -> None:
        if self.movie_info == movie_info:
            return

        self.movie_info = movie_info
        self.build_from_movie_info(movie_info)

    def build(self, folder_path: str) -> None:
        self.setStyleSheet(APP_THEME.container_qss())
        parsed_movie_info = self.nfo_parse_util.parse_nfo(folder_path=folder_path)
        self.set_movie_info(parsed_movie_info)

        self.apply_theme()

    def clear_nfo(self) -> None:
        self.scroll_content_widget.clear_for_empty_nfo()
        self.toolbar_widget.rebuild_for_view_mode(self.view_mode)

    def build_from_movie_info(self, movie_info: dict) -> None:
        if not movie_info:
            self.clear_nfo()
            return

        self.toolbar_widget.rebuild_for_view_mode(self.view_mode)
        QTimer.singleShot(150, lambda: self._build_or_update_sections(movie_info))

    def set_view_mode(self, mode: str) -> None:
        if self.view_mode == mode:
            return

        self.view_mode = mode
        self.toolbar_widget.rebuild_for_view_mode(self.view_mode)

        if self.movie_info:
            self.build_from_movie_info(self.movie_info)

    def play_video(self, payload: SignalPayload = None) -> None:
        self.sig_info_play_video_btn_clicked.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Play Video Requested",
                description="Emitted when play video button is clicked in view.",
                flow=SignalFlow.USER_INPUT,
            )
        )

    def apply_theme(self) -> None:
        super().apply_theme()

        self.common_section.apply_theme()
        self.plot_section.apply_theme()
        self.ids_section.apply_theme()
        self.videos_section.apply_theme()
        self.audios_section.apply_theme()
        self.subtitles_section.apply_theme()
        self.actors_section.apply_theme()

    def _build_or_update_sections(self, movie_info: dict) -> None:
        self._build_common_section(movie_info)
        self._build_ids_section(movie_info)
        self._build_plot_section(movie_info)
        self._build_media_stream_sections(movie_info)
        self._build_actors_section(movie_info)

        self.scroll_content_widget.ensure_trailing_stretch()

    def _build_common_section(self, movie_info: dict) -> None:
        self.common_section.build(movie_info, self.view_mode)
        self.scroll_content_widget.add_section_if_missing(
            MEDIA_INFO_SECTION_COMMON,
            self.common_section,
        )
        self.common_section.apply_theme()

    def _build_ids_section(self, movie_info: dict) -> None:
        self.ids_section.build_ids(movie_info.get("ids", []))
        self.scroll_content_widget.add_section_if_missing(
            MEDIA_INFO_SECTION_IDS,
            self.ids_section,
        )
        self.ids_section.apply_theme()

    def _build_plot_section(self, movie_info: dict) -> None:
        self.plot_section.build(movie_info.get("plot", ""))
        self.scroll_content_widget.add_section_if_missing(
            MEDIA_INFO_SECTION_PLOT,
            self.plot_section,
        )
        self.plot_section.apply_theme()

    def _build_media_stream_sections(self, movie_info: dict) -> None:
        if self.view_mode == MEDIA_INFO_VIEW_MODE_IMAGE_LIST:
            self._remove_sections_hidden_in_image_list()
            return

        self.videos_section.build_videos(movie_info.get("videos", []))
        self.scroll_content_widget.add_section_if_missing(
            MEDIA_INFO_SECTION_VIDEOS,
            self.videos_section,
        )
        self.videos_section.apply_theme()

        self.audios_section.build_audios(movie_info.get("audios", []))
        self.scroll_content_widget.add_section_if_missing(
            MEDIA_INFO_SECTION_AUDIOS,
            self.audios_section,
        )
        self.audios_section.apply_theme()

        self.subtitles_section.build_subtitles(movie_info.get("subtitles", []))
        self.scroll_content_widget.add_section_if_missing(
            MEDIA_INFO_SECTION_SUBTITLES,
            self.subtitles_section,
        )
        self.subtitles_section.apply_theme()

    def _remove_sections_hidden_in_image_list(self) -> None:
        for section_id in MEDIA_INFO_SECTIONS_HIDDEN_IN_IMAGE_LIST:
            self.scroll_content_widget.remove_section_if_present(section_id)

    def _build_actors_section(self, movie_info: dict) -> None:
        self.actors_section.build(movie_info.get("actors", []))
        self.scroll_content_widget.add_section_if_missing(
            MEDIA_INFO_SECTION_ACTORS,
            self.actors_section,
        )
        self.actors_section.apply_theme()

    def _toggle_section(self, section_id: str) -> None:
        is_section_visible = self.scroll_content_widget.toggle_section_visibility(
            section_id
        )

        if is_section_visible is not None:
            self.toolbar_widget.set_section_toggle_checked(
                section_id, is_section_visible
            )
