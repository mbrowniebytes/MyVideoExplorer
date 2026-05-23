from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.utils.nfo_parse_util import NfoParseUtil
from src.utils.str_util import StrUtil
from src.theme.theme import APP_THEME
from src.media_info.media_info_common_section import MediaInfoCommonSection
from src.media_info.media_info_plot_section import MediaInfoPlotSection
from src.media_info.media_info_details_section import MediaInfoDetailsSection
from src.media_info.media_info_actors_section import MediaInfoActorsSection


class MediaInfoView(QWidget):
    sig_info_play_video_btn_clicked = Signal()

    def __init__(self, nfo_parse_util: NfoParseUtil, str_util: StrUtil, log_util=None) -> None:
        super().__init__()
        self.log_util = log_util
        if self.log_util:
            self.log_util.debug(f"__init__ {self.__class__.__name__}")

        self.section_widgets: dict[str, QFrame] = {}
        self.toggle_layout = QHBoxLayout()
        self.toggle_layout.setContentsMargins(0, 0, 0, 0)

        self.content_container = QWidget()
        self.content_container.setStyleSheet(APP_THEME.container_qss())

        self.media_info_layout = QVBoxLayout(self.content_container)
        self.media_info_layout.setContentsMargins(0, 0, 0, 0)
        self.media_info_layout.setSpacing(4)
        self.media_info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.content_container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(self.toggle_layout)
        main_layout.addWidget(self.scroll_area)

        self.nfo_parse_util = nfo_parse_util
        self.str_util = str_util
        self.movie_info: dict = {}
        self.view_mode = "media_info"

        # Initialize sub-sections
        self.common_section = MediaInfoCommonSection(self.str_util)
        self.plot_section = MediaInfoPlotSection()
        self.ids_section = MediaInfoDetailsSection()
        self.videos_section = MediaInfoDetailsSection()
        self.audios_section = MediaInfoDetailsSection()
        self.subtitles_section = MediaInfoDetailsSection()
        self.actors_section = MediaInfoActorsSection()

    def refresh(self, folder_path: str) -> None:
        nfo = self.nfo_parse_util.parse_nfo(folder_path=folder_path)
        self.set_movie_info(nfo)

    def set_movie_info(self, movie_info: dict) -> None:
        if self.movie_info == movie_info:
            return
        self.movie_info = movie_info
        self.build_from_movie_info(movie_info)

    def build(self, folder_path: str) -> None:
        self.setStyleSheet(APP_THEME.container_qss())
        nfo = self.nfo_parse_util.parse_nfo(folder_path=folder_path)
        self.set_movie_info(nfo)

    def clear_nfo(self) -> None:
        self._clear_layout(self.media_info_layout)
        self._clear_layout(self.toggle_layout)
        self.section_widgets.clear()

        placeholder = QLabel("No NFO data found")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._show_placeholder(placeholder, "No NFO data found")
        self.media_info_layout.addWidget(placeholder)

    def build_from_movie_info(self, nfo: dict) -> None:
        """Builds all UI components from the movie info dictionary."""
        if not nfo:
            self.clear_nfo()
            return

        # Ensure toggle buttons are built
        if self.toggle_layout.count() == 0:
            self._build_toggle_buttons()

        # Update or add sections
        self._ensure_sections_built(nfo)

    def _ensure_sections_built(self, nfo: dict) -> None:
        """Ensures all sections are built and added to the layout."""
        # 1. Common Section
        self.common_section.build(nfo, self.view_mode)
        if "section_common" not in self.section_widgets:
            self._add_section("section_common", self.common_section)

        # 2. IDs Section
        self.ids_section.build_ids(nfo.get("ids", []))
        if "section_ids" not in self.section_widgets:
            self._add_section("section_ids", self.ids_section)

        # 3. Plot Section
        self.plot_section.build(nfo.get("plot", ""))
        if "section_plot" not in self.section_widgets:
            self._add_section("section_plot", self.plot_section)

        if self.view_mode != "image_list":
            # 4. Videos Section
            self.videos_section.build_videos(nfo.get("videos", []))
            if "section_videos" not in self.section_widgets:
                self._add_section("section_videos", self.videos_section)

            # 5. Audios Section
            self.audios_section.build_audios(nfo.get("audios", []))
            if "section_audios" not in self.section_widgets:
                self._add_section("section_audios", self.audios_section)

            # 6. Subtitles Section
            self.subtitles_section.build_subtitles(nfo.get("subtitles", []))
            if "section_subtitles" not in self.section_widgets:
                self._add_section("section_subtitles", self.subtitles_section)
        else:
            # Remove sections not used in image_list if they were there
            for sid in ["section_videos", "section_audios", "section_subtitles"]:
                if sid in self.section_widgets:
                    widget = self.section_widgets.pop(sid)
                    self.media_info_layout.removeWidget(widget)
                    widget.setParent(None)

        # 7. Actors Section
        self.actors_section.build(nfo.get("actors", []))
        if "section_actors" not in self.section_widgets:
            self._add_section("section_actors", self.actors_section)

        # Ensure stretch is at the end
        if (
            self.media_info_layout.itemAt(
                self.media_info_layout.count() - 1
            ).spacerItem()
            is None
        ):
            self.media_info_layout.addStretch()

    def _add_section(self, name: str, widget: QFrame) -> None:
        self.section_widgets[name] = widget
        # The Actors section gets a stretch factor of 1, others 0
        stretch = 1 if name == "section_actors" else 0
        self.media_info_layout.addWidget(widget, stretch)

    def set_view_mode(self, mode: str) -> None:
        self.view_mode = mode

    def _show_placeholder(self, widget: QLabel, text: str) -> None:
        widget.setPixmap(QPixmap())
        widget.setText(text)

    def _build_toggle_buttons(self) -> None:
        sections = [
            ("section_common", "Common"),
            ("section_plot", "Plot"),
            ("section_ids", "IDs"),
        ]
        if self.view_mode != "image_list":
            sections += [
                ("section_videos", "Videos"),
                ("section_audios", "Audios"),
                ("section_subtitles", "Subtitles"),
            ]
        sections.append(("section_actors", "Actors"))

        for section_id, label in sections:
            self._add_toggle_button(section_id, label)

        self._add_play_button()

    def _add_toggle_button(self, section_id: str, label: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setChecked(True)
        btn.setFixedSize(100, 25)
        btn.clicked.connect(lambda: self._toggle_section(section_id))
        btn.setStyleSheet(APP_THEME.small_button_qss())
        self.toggle_layout.addWidget(btn)
        return btn

    def _toggle_section(self, section_id: str) -> None:
        widget = self.section_widgets.get(section_id)
        if widget:
            widget.setVisible(not widget.isVisible())

    def _add_play_button(self) -> None:
        play_btn = QPushButton("▶")
        play_btn.setMinimumWidth(40)
        play_btn.setStyleSheet(APP_THEME.small_button_qss())
        play_btn.clicked.connect(self.play_video)
        self.toggle_layout.addStretch(1)
        self.toggle_layout.addWidget(play_btn)

    def play_video(self) -> None:
        self.sig_info_play_video_btn_clicked.emit()

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                # We do NOT deleteLater() here if the widget is one of our persistent sections
                # To be safe and simple, we just setParent(None) for all widgets
                item.widget().setParent(None)
            elif item.layout():
                self._clear_layout(item.layout())

    def apply_theme(self) -> None:
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.setStyleSheet(APP_THEME.container_qss())
        self.setFont(font)

        self.plot_section.apply_theme()

        self._refresh_child_fonts(self, font)

    def _refresh_child_fonts(self, widget: QWidget, font: QFont) -> None:
        for child in widget.findChildren(QWidget):
            if isinstance(child, (QLabel, QPushButton)):
                child.setFont(font)
            # SimpleTable handles its own theme
            if hasattr(child, "apply_theme") and child != self:
                child.apply_theme()
