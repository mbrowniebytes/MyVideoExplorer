from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.db.db_play_history import DbPlayHistory
from MyVideoExplorer.db.db_tags import DbTags
from MyVideoExplorer.db.models.play_history import PlayHistory
from MyVideoExplorer.media_info_section.media_info_section_definitions import (
    MEDIA_INFO_VIEW_MODE_IMAGE_LIST,
)
from MyVideoExplorer.media_info_section.media_info_section_plot import (
    MediaInfoPlotSection,
)
from MyVideoExplorer.media_info_side.media_info_side_content_widget import (
    MediaInfoSideContentWidget,
)
from MyVideoExplorer.tag_cloud.tag_cloud_media import TagStateProtocol
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.utils.str_util import StrUtil
from MyVideoExplorer.utils.ui_utils import UIUtils
from MyVideoExplorer.widgets.label_value_widget import LabelValueWidget


class MediaInfoSideView(QWidget, ThemableMixin):
    """
    Side view displaying metadata and quick actions for a media item.
    """

    info_side_play_video_btn_clicked = Signal(object)

    def __init__(
        self,
        nfo_parse_util: NfoParseUtil,
        str_util: StrUtil,
        log_util,
        play_history: DbPlayHistory | None = None,
        tag_store: DbTags | None = None,
        tag_state: TagStateProtocol | None = None,
    ) -> None:
        super().__init__()
        self.log_util = log_util
        self._ui_utils = UIUtils()

        self.nfo_parse_util = nfo_parse_util
        self.str_util = str_util
        self.play_history = play_history
        self.tag_store = tag_store
        self.tag_state = tag_state
        self.media_file_path = ""

        self.current_movie_info: dict | None = None
        self.current_view_mode = MEDIA_INFO_VIEW_MODE_IMAGE_LIST

        # Make child widgets owned by this view to avoid creating top-level windows
        self.side_content_widget = MediaInfoSideContentWidget(
            self.str_util,
            parent=self,
            tag_state=tag_state,
            tag_store=tag_store,
        )
        self.side_content_widget.hide()
        self.side_content_widget.column_widths_changed.connect(self.setFixedWidth)

        self.empty_nfo_placeholder_widget = LabelValueWidget(
            name="",
            value="No NFO data found",
            orientation=Qt.Orientation.Vertical,
            parent=self,
        )

        self.plot_section = MediaInfoPlotSection()

        self.media_info_side_layout = self._ui_utils.apply_compact_layout(
            self, QVBoxLayout
        )
        self.media_info_side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.media_info_side_layout.setContentsMargins(0, 10, 0, 5)

        self.media_info_side_layout.addWidget(self.side_content_widget)
        self.media_info_side_layout.addWidget(self.empty_nfo_placeholder_widget)

        self.setFixedWidth(300)
        self.side_content_widget.played_count_changed.connect(self._save_played_count)
        self.side_content_widget.last_played_changed.connect(self._save_last_played)
        self.side_content_widget.tag_cloud_widget.tag_added.connect(self._add_media_tag)
        self.side_content_widget.tag_cloud_widget.tag_removed.connect(
            self._remove_media_tag
        )
        if self.tag_state is not None:
            self.tag_state.tags_changed.connect(self._refresh_current_media_tags)

        # Backward-compatible aliases for existing tests/callers.
        self.movie_info = self.current_movie_info
        self.view_mode = self.current_view_mode

    def refresh(self, folder_path: str) -> None:
        """Parse and display NFO information for the given folder."""
        parsed_movie_info = self.nfo_parse_util.parse_nfo(folder_path=folder_path)
        self.set_movie_info(parsed_movie_info)

    def set_movie_info(self, movie_info: dict | None) -> None:
        """Set movie info and update the side view if the data changed."""
        if self.current_movie_info == movie_info:
            return

        self.current_movie_info = movie_info

        # Backward-compatible alias.
        self.movie_info = self.current_movie_info

        self.build_from_movie_info(movie_info)

    def build(self, folder_path: str) -> None:
        """Build the side view for a given folder path."""
        self.apply_theme()
        self.refresh(folder_path)

    def clear_nfo(self) -> None:
        """Clear NFO details while keeping the play-history metadata visible."""
        self.side_content_widget.show()
        self.side_content_widget.set_nfo_available(False)
        self.plot_section.build("")
        self.empty_nfo_placeholder_widget.show()

    def build_nfo(self, movie_info: dict | None) -> None:
        """Backward-compatible wrapper for updating from a movie info dictionary."""
        self.build_from_movie_info(movie_info)

    def get_plot_section(self) -> MediaInfoPlotSection:
        """Return the plot section widget."""
        return self.plot_section

    def set_plot_text(self, movie_info: dict | None) -> None:
        """Update the cached plot section from movie info data."""
        if movie_info:
            self.plot_section.build(movie_info.get("plot", ""))

    def build_from_movie_info(self, movie_info: dict | None) -> None:
        """Build or update side view widgets from movie info data."""
        if not movie_info:
            self.clear_nfo()
            return

        self._ensure_side_content_widget()
        self.side_content_widget.set_nfo_available(True)
        self.side_content_widget.update_from_movie_info(movie_info)
        self.set_plot_text(movie_info)

    def set_media_file_path(self, file_path: str | None) -> None:
        """Load play history for the currently selected video's indexed record."""
        self.media_file_path = file_path or ""
        history = (
            self.play_history.get_history(self.media_file_path)
            if self.play_history and self.media_file_path
            else None
        )
        self._display_play_history(history)
        tags = (
            self.tag_store.get_tags(self.media_file_path)
            if self.tag_store and self.media_file_path
            else None
        )
        self.side_content_widget.tag_cloud_widget.set_tags(tags)
        self.side_content_widget.tag_cloud_widget.set_enabled(
            self.tag_store is not None
            and bool(self.media_file_path)
            and tags is not None
        )

    def refresh_play_history(self) -> None:
        """Reload the displayed history after playback updates the database."""
        self.set_media_file_path(self.media_file_path)

    def _refresh_current_media_tags(self) -> None:
        if not self.tag_store or not self.media_file_path:
            return
        tags = self.tag_store.get_tags(self.media_file_path)
        if tags is not None:
            self.side_content_widget.tag_cloud_widget.set_tags(tags)

    def set_view_mode(self, mode: str) -> None:
        """Set the current view mode."""
        self.current_view_mode = mode

        # Backward-compatible alias.
        self.view_mode = self.current_view_mode

    def play_video(self, payload: SignalPayload | None = None) -> None:
        """Emit the side-view play-video signal."""
        self.info_side_play_video_btn_clicked.emit(
            payload
            or SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Play Video Requested",
                description="Emitted when play video button is clicked in side view.",
                flow=SignalFlow.USER_INPUT,
            )
        )

    def apply_theme(self) -> None:
        """Apply theme to this view and child widgets."""
        if not APP_THEME.is_refreshing:
            super().apply_theme()
            return

        self.plot_section.apply_theme()

    def _ensure_side_content_widget(self) -> None:
        self.empty_nfo_placeholder_widget.hide()
        self.side_content_widget.show()

    def _display_play_history(self, history: PlayHistory | None) -> None:
        controls = (
            self.side_content_widget.played_spin_box,
            self.side_content_widget.last_played_date_edit,
        )
        for control in controls:
            control.blockSignals(True)

        if history is None:
            self.side_content_widget.played_spin_box.setValue(0)
            self.side_content_widget.last_played_date_edit.setDate(
                self.side_content_widget.last_played_date_edit.minimumDate()
            )
        else:
            self.side_content_widget.played_spin_box.setValue(history.qty_played)
            played_date = history.last_played
            self.side_content_widget.last_played_date_edit.setDate(
                QDate.fromString(played_date.isoformat(), "yyyy-MM-dd")
                if played_date
                else self.side_content_widget.last_played_date_edit.minimumDate()
            )

        for control in controls:
            control.blockSignals(False)
            control.setEnabled(history is not None and self.play_history is not None)

    def _save_played_count(self, qty_played: int) -> None:
        if not self.play_history or not self.media_file_path:
            return
        if not self.play_history.set_qty_played(self.media_file_path, qty_played):
            self.log_util.warning(
                f"Could not save play count for {self.media_file_path}"
            )

    def _save_last_played(self, played_date: QDate) -> None:
        if not self.play_history or not self.media_file_path:
            return
        last_played: date | None = (
            None
            if played_date
            == self.side_content_widget.last_played_date_edit.minimumDate()
            else date.fromisoformat(played_date.toString("yyyy-MM-dd"))
        )
        if not self.play_history.set_last_played(self.media_file_path, last_played):
            self.log_util.warning(
                f"Could not save last-played date for {self.media_file_path}"
            )

    def _add_media_tag(self, tag: str) -> None:
        tag_widget = self.side_content_widget.tag_cloud_widget
        tags = tag_widget.tags
        if tag.casefold() in {existing.casefold() for existing in tags}:
            return
        updated_tags = [*tags, tag]
        if not self.tag_store or not self.media_file_path:
            return
        if not self.tag_store.set_tags(self.media_file_path, updated_tags):
            self.log_util.warning(f"Could not save tags for {self.media_file_path}")
            return
        tag_widget.set_tags(updated_tags)
        if self.tag_state is not None:
            self.tag_state.tag_counts_changed.emit()

    def _remove_media_tag(self, tag: str) -> None:
        tag_widget = self.side_content_widget.tag_cloud_widget
        updated_tags = [
            existing
            for existing in tag_widget.tags
            if existing.casefold() != tag.casefold()
        ]
        if len(updated_tags) == len(tag_widget.tags):
            return
        if not self.tag_store or not self.media_file_path:
            return
        if not self.tag_store.set_tags(self.media_file_path, updated_tags):
            self.log_util.warning(f"Could not save tags for {self.media_file_path}")
            return
        tag_widget.set_tags(updated_tags)
        if self.tag_state is not None:
            self.tag_state.tag_counts_changed.emit()
