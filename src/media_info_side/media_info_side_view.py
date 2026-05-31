from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QVBoxLayout

from src.media_info_section.media_info_section_plot import MediaInfoPlotSection
from src.media_info_section.media_info_section_definitions import MEDIA_INFO_VIEW_MODE_IMAGE_LIST
from src.media_info_side.media_info_side_content_widget import MediaInfoSideContentWidget
from src.theme.theme import APP_THEME
from src.utils.nfo_parse_util import NfoParseUtil
from src.utils.str_util import StrUtil
from src.widgets.base_widget import BaseWidget
from src.widgets.label_value_widget import LabelValueWidget


class MediaInfoSideView(BaseWidget):
    """
    Side view displaying metadata and quick actions for a media item.
    """

    sig_info_side_play_video_btn_clicked = Signal()

    def __init__(self, nfo_parse_util: NfoParseUtil, str_util: StrUtil, log_util) -> None:
        super().__init__(log_util)

        self.nfo_parse_util = nfo_parse_util
        self.str_util = str_util

        self.current_movie_info: dict = {}
        self.current_view_mode = MEDIA_INFO_VIEW_MODE_IMAGE_LIST

        self.side_content_widget: MediaInfoSideContentWidget | None = None
        self.empty_nfo_placeholder_widget: LabelValueWidget | None = None

        self.plot_section = MediaInfoPlotSection()

        self.media_info_side_layout = self.set_compact_layout(QVBoxLayout)
        self.media_info_side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setFixedWidth(85)

        # Backward-compatible aliases for existing tests/callers.
        self.movie_info = self.current_movie_info
        self.view_mode = self.current_view_mode

    def refresh(self, folder_path: str) -> None:
        """Parse and display NFO information for the given folder."""
        parsed_movie_info = self.nfo_parse_util.parse_nfo(folder_path=folder_path)
        self.set_movie_info(parsed_movie_info)

    def set_movie_info(self, movie_info: dict) -> None:
        """Set movie info and update the side view if the data changed."""
        if self.current_movie_info == movie_info:
            return

        self.current_movie_info = movie_info

        # Backward-compatible alias.
        self.movie_info = self.current_movie_info

        self.build_from_movie_info(movie_info)

    def build(self, folder_path: str) -> None:
        """Build the side view for a given folder path."""
        self.setStyleSheet(APP_THEME.container_qss())
        self.refresh(folder_path)

    def clear_nfo(self) -> None:
        """Clear current NFO widgets and display an empty-data placeholder."""
        self.clear_layout(self.media_info_side_layout)
        self.side_content_widget = None

        self.plot_section.build("")

        self.empty_nfo_placeholder_widget = LabelValueWidget(
            name="",
            value="No NFO data found",
            orientation=Qt.Orientation.Vertical,
        )
        self.media_info_side_layout.addWidget(self.empty_nfo_placeholder_widget)

    def build_nfo(self, movie_info: dict) -> None:
        """Backward-compatible wrapper for updating from a movie info dictionary."""
        self.build_from_movie_info(movie_info)

    def get_plot_section(self) -> MediaInfoPlotSection:
        """Return the plot section widget."""
        return self.plot_section

    def set_plot_text(self, movie_info: dict) -> None:
        """Update the cached plot section from movie info data."""
        self.plot_section.build(movie_info.get("plot", ""))

    def build_from_movie_info(self, movie_info: dict) -> None:
        """Build or update side view widgets from movie info data."""
        if not movie_info:
            self.clear_nfo()
            return

        self._ensure_side_content_widget()
        self.side_content_widget.update_from_movie_info(movie_info)
        self.set_plot_text(movie_info)

    def set_view_mode(self, mode: str) -> None:
        """Set the current view mode."""
        self.current_view_mode = mode

        # Backward-compatible alias.
        self.view_mode = self.current_view_mode

    def play_video(self) -> None:
        """Emit the side-view play-video signal."""
        self.sig_info_side_play_video_btn_clicked.emit()

    def apply_theme(self) -> None:
        """Apply theme to this view and child widgets."""
        super().apply_theme()

        application_font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.setFont(application_font)

        self.plot_section.apply_theme()

        if self.side_content_widget is not None:
            self.side_content_widget.apply_theme()

        if self.empty_nfo_placeholder_widget is not None:
            self.empty_nfo_placeholder_widget.setFont(application_font)

    def _ensure_side_content_widget(self) -> None:
        if self.side_content_widget is not None:
            return

        self.clear_layout(self.media_info_side_layout)

        self.side_content_widget = MediaInfoSideContentWidget(self.str_util)
        self.side_content_widget.sig_play_video_requested.connect(self.play_video)

        self.media_info_side_layout.addWidget(self.side_content_widget)
        self.media_info_side_layout.addStretch()
