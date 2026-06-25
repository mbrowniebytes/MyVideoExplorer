from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from MyVideoExplorer.media_info.media_info_id_link_formatter import MediaInfoIdLinkFormatter
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.str_util import StrUtil
from MyVideoExplorer.widgets.base_widget import BaseWidget
from MyVideoExplorer.widgets.label_value_widget import LabelValueWidget


class MediaInfoSideFactsWidget(BaseWidget):
    """Compact metadata facts displayed in the narrow media info side panel."""

    FIXED_FIELD_DEFINITIONS = [
        ("Score", "rating"),
        ("MPAA", "mpaa"),
        ("Runtime", "runtime"),
        ("Genres", "genres"),
    ]

    def __init__(
        self,
        str_util: StrUtil,
        id_link_formatter: MediaInfoIdLinkFormatter | None = None,
        log_util: LogUtil | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(log_util or LogUtil(), parent)

        self.str_util = str_util
        self.id_link_formatter = id_link_formatter or MediaInfoIdLinkFormatter()

        self.fixed_field_widgets_by_key: dict[str, LabelValueWidget] = {}
        self.dynamic_id_value_widgets: list[LabelValueWidget] = []

        self.facts_layout = QVBoxLayout(self)
        self.facts_layout.setContentsMargins(0, 0, 0, 0)
        self.facts_layout.setSpacing(0)

        self._build_fixed_field_widgets()
        self.facts_layout.addStretch()

        self.apply_theme()

    def update_from_movie_info(self, movie_info: dict) -> None:
        self._update_fixed_field_values(movie_info)
        self._update_id_widgets(movie_info.get("ids", []))

    def apply_theme(self) -> None:
        super().apply_theme()
        self.setStyleSheet(APP_THEME.container_qss())

    def _build_fixed_field_widgets(self) -> None:
        for field_label, movie_info_key in self.FIXED_FIELD_DEFINITIONS:
            field_value_widget = LabelValueWidget(
                name=field_label,
                value="",
                orientation=Qt.Orientation.Vertical,
                log_util=self.log_util,
                parent=self,
            )
            self.fixed_field_widgets_by_key[movie_info_key] = field_value_widget
            self.facts_layout.addWidget(field_value_widget)

    def _update_fixed_field_values(self, movie_info: dict) -> None:
        self.fixed_field_widgets_by_key["rating"].set_value(movie_info.get("rating", ""))
        self.fixed_field_widgets_by_key["mpaa"].set_value(movie_info.get("mpaa", ""))
        self.fixed_field_widgets_by_key["runtime"].set_value(movie_info.get("runtime", ""))

        genre_values = movie_info.get("genres", [])
        self.fixed_field_widgets_by_key["genres"].set_value(
            self.str_util.join_strings(genre_values)
        )

    def _update_id_widgets(self, media_id_items: list[dict]) -> None:
        formatted_id_html_values = self.id_link_formatter.build_id_html_values(media_id_items)

        self._remove_excess_id_widgets(len(formatted_id_html_values))

        for id_index, formatted_id_html_value in enumerate(formatted_id_html_values):
            media_id_type = media_id_items[id_index].get("type", "")
            id_label_text = (
                ""
                if self.id_link_formatter.should_hide_id_label(media_id_type)
                else "ID"
            )

            if id_index < len(self.dynamic_id_value_widgets):
                id_value_widget = self.dynamic_id_value_widgets[id_index]
                id_value_widget.label_name.setText(id_label_text)
                id_value_widget.label_name.setVisible(bool(id_label_text))
                id_value_widget.set_value(formatted_id_html_value)
            else:
                self._add_id_widget(id_label_text, formatted_id_html_value)

    def _remove_excess_id_widgets(self, expected_id_widget_count: int) -> None:
        while len(self.dynamic_id_value_widgets) > expected_id_widget_count:
            id_value_widget = self.dynamic_id_value_widgets.pop()
            self.facts_layout.removeWidget(id_value_widget)
            id_value_widget.deleteLater()

    def _add_id_widget(self, id_label_text: str, formatted_id_html_value: str) -> None:
        id_value_widget = LabelValueWidget(
            name=id_label_text,
            value=formatted_id_html_value,
            orientation=Qt.Orientation.Vertical,
            is_link=True,
            log_util=self.log_util,
            parent=self,
        )

        stretch_index = max(0, self.facts_layout.count() - 1)
        self.facts_layout.insertWidget(stretch_index, id_value_widget)
        self.dynamic_id_value_widgets.append(id_value_widget)
