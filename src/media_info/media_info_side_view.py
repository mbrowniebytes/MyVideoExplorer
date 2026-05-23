from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QPushButton,
    QVBoxLayout,
    QLabel,
)

from src.utils.nfo_parse_util import NfoParseUtil
from src.utils.str_util import StrUtil
from src.widgets.label_value_widget import LabelValueWidget
from src.theme.theme import APP_THEME
from src.media_info.media_info_plot_section import MediaInfoPlotSection
from src.widgets.base_widget import BaseWidget


class MediaInfoSideView(BaseWidget):
    """
    Side view displaying metadata and quick actions for a media item.
    """

    sig_info_side_play_video_btn_clicked = Signal()

    def __init__(self, nfo_parse_util: NfoParseUtil, str_util: StrUtil, log_util) -> None:
        super().__init__(log_util)
        self._current_nfo: dict = {}
        self.nfo_parse_util = nfo_parse_util
        self.str_util = str_util
        self.movie_info: dict = {}
        self.view_mode = "image_list"

        self.plot_section = MediaInfoPlotSection()
        self.media_info_side_layout = self.set_compact_layout(QVBoxLayout)
        self.media_info_side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setFixedWidth(85)

    def refresh(self, folder_path: str) -> None:
        """Parses and updates the NFO information for the given folder."""
        nfo = self.nfo_parse_util.parse_nfo(folder_path=folder_path)
        self.set_movie_info(nfo)

    def set_movie_info(self, movie_info: dict) -> None:
        """Sets the movie info and updates the view."""
        self.movie_info = movie_info
        self.build_from_movie_info(movie_info)

    def build(self, folder_path: str) -> None:
        """Builds the view for a given folder path."""
        self.setStyleSheet(APP_THEME.container_qss())
        self.refresh(folder_path)

    def clear_nfo(self) -> None:
        """Clears current NFO data and displays a placeholder."""
        self.clear_layout(self.media_info_side_layout)
        self.plot_section.build("")
        placeholder = LabelValueWidget(
            name="", value="No NFO data found", orientation=Qt.Orientation.Vertical
        )
        self.media_info_side_layout.addWidget(placeholder)

    def build_nfo(self, nfo: dict) -> None:
        """Updates the view with provided NFO dictionary."""
        self.build_from_movie_info(nfo)

    def get_plot_section(self) -> MediaInfoPlotSection:
        """Returns the plot section widget."""
        return self.plot_section

    def set_plot_text(self, nfo: dict) -> None:
        """Updates the plot text from NFO data."""
        plot = nfo.get("plot", "")
        self.plot_section.build(plot)

    def build_from_movie_info(self, nfo: dict) -> None:
        """Builds all UI components from the movie info dictionary."""
        if hasattr(self, "_current_nfo") and self._current_nfo == nfo:
            return
        self._current_nfo = nfo

        if not nfo:
            self.clear_nfo()
            return

        self._ensure_side_info_frame()
        self._update_side_info_values(nfo)
        self.set_plot_text(nfo)

    def _ensure_side_info_frame(self) -> None:
        """Ensures the side info frame and its basic layout exist."""
        info_frame = self.findChild(QFrame, "side_media_info")
        if not info_frame:
            self.clear_layout(self.media_info_side_layout)
            self._build_side_info_frame()

    def _build_side_info_frame(self) -> None:
        """Creates the base frame and basic widgets for side info."""
        info_frame = QFrame()
        info_frame.setObjectName("side_media_info")
        info_frame.setStyleSheet(APP_THEME.container_qss())

        frame_layout = QVBoxLayout(info_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # 1. Play button
        frame_layout.addWidget(self._create_play_button())

        label_title = QLabel("NFO")
        label_title.setWordWrap(False)
        label_title.setStyleSheet(APP_THEME.secondary_label_qss())
        label_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        frame_layout.addWidget(label_title)

        # 2. Fixed fields
        fields = [
            ("Score", "rating"),
            ("MPAA", "mpaa"),
            ("Runtime", "runtime"),
            ("Genres", "genres"),
        ]

        for label, _ in fields:
            frame_layout.addWidget(
                LabelValueWidget(
                    name=label,
                    value="",
                    orientation=Qt.Orientation.Vertical,
                )
            )

        # 3. ID labels (placeholder for them)
        # We'll handle IDs dynamically in update

        frame_layout.addStretch()
        self.media_info_side_layout.addWidget(info_frame)
        self.media_info_side_layout.addStretch()

    def _update_side_info_values(self, nfo: dict) -> None:
        """Updates the values of existing widgets in the side info frame."""
        info_frame = self.findChild(QFrame, "side_media_info")
        if not info_frame:
            return

        frame_layout = info_frame.layout()
        widgets = []
        for i in range(frame_layout.count()):
            w = frame_layout.itemAt(i).widget()
            if isinstance(w, LabelValueWidget):
                widgets.append(w)

        # Base fields: Score, MPAA, Runtime, Genres
        if len(widgets) >= 4:
            widgets[0].set_value(nfo.get("rating", ""))
            widgets[1].set_value(nfo.get("mpaa", ""))
            widgets[2].set_value(nfo.get("runtime", ""))
            widgets[3].set_value(self.str_util.join_strings(nfo.get("genres", [])))

        # Handle IDs
        ids = nfo.get("ids", [])
        id_htmls = self._get_id_htmls(ids)
        expected_base_fields = 4

        # Remove excess ID widgets
        while len(widgets) > expected_base_fields + len(id_htmls):
            w = widgets.pop()
            frame_layout.removeWidget(w)
            w.deleteLater()

        # Update existing ID widgets or add new ones
        for i, id_html in enumerate(id_htmls):
            widget_idx = expected_base_fields + i
            if widget_idx < len(widgets):
                widgets[widget_idx].set_value(id_html)
                # Also update label just in case
                id_type = ids[i].get("type", "")
                widgets[widget_idx].label_name.setText(
                    "" if id_type in ["imdbid", "tmdbid"] else "ID"
                )
            else:
                id_type = ids[i].get("type", "")
                new_widget = LabelValueWidget(
                    name="" if id_type in ["imdbid", "tmdbid"] else "ID",
                    value=id_html,
                    orientation=Qt.Orientation.Vertical,
                    is_link=True,
                )
                # Insert before the stretch (which is the last item)
                frame_layout.insertWidget(frame_layout.count() - 1, new_widget)
                widgets.append(new_widget)

    def set_view_mode(self, mode: str) -> None:
        """Sets the current view mode."""
        self.view_mode = mode

    def _get_id_htmls(self, ids: list[dict]) -> list[str]:
        htmls = []
        for item in ids:
            id_type = item.get("type", "")
            id_val = item.get("id", "")
            if id_type == "imdbid":
                htmls.append(
                    f'<a href="https://www.imdb.com/title/{id_val}/">IMDb</a> '
                )
            elif id_type == "tmdbid":
                htmls.append(
                    f'<a href="https://www.themoviedb.org/movie/{id_val}/">TMDB</a> '
                )
            else:
                htmls.append(f"<i>{id_type}</i> ")
        return htmls

    def _build_side_ids_labels(self, ids: list[dict]) -> list[LabelValueWidget]:
        if not ids:
            return []

        id_labels = []
        id_htmls = self._get_id_htmls(ids)
        for i, id_html in enumerate(id_htmls):
            id_type = ids[i].get("type", "")
            id_labels.append(
                LabelValueWidget(
                    name="" if id_type in ["imdbid", "tmdbid"] else "ID",
                    value=id_html,
                    orientation=Qt.Orientation.Vertical,
                    is_link=True,
                )
            )

        return id_labels

    def _create_play_button(self) -> QPushButton:
        play_button = QPushButton("▶")
        play_button.setMinimumWidth(40)
        play_button.setStyleSheet(APP_THEME.small_button_qss())
        play_button.clicked.connect(self.play_video)
        return play_button

    def play_video(self) -> None:
        """Emits signal to play video."""
        self.sig_info_side_play_video_btn_clicked.emit()

    def apply_theme(self) -> None:
        """Applies theme to the view and sub-components."""
        super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.setFont(font)
        self.plot_section.apply_theme()
