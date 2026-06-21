from __future__ import annotations

import pathlib

from PySide6.QtWidgets import QFrame, QHeaderView, QSizePolicy, QVBoxLayout, QWidget

from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.widgets.label_value_widget import LabelValueWidget
from MyVideoExplorer.widgets.simple_table_widget import SimpleTableWidget


ACTOR_TABLE_COLUMN_KEYS = ["order", "name", "role", "thumb"]
ACTOR_TABLE_COLUMN_HEADERS = ["#", "Name", "Role", "Thumb"]
ACTOR_TABLE_COLUMN_RESIZE_MODES = [
    QHeaderView.ResizeMode.ResizeToContents,
    QHeaderView.ResizeMode.Stretch,
    QHeaderView.ResizeMode.Stretch,
    QHeaderView.ResizeMode.ResizeToContents,
]


class MediaInfoActorsSection(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._current_actor_items: list[dict] = []
        self.actors_title_widget: LabelValueWidget | None = None
        self.actors_table_widget: SimpleTableWidget | None = None

        self.actors_section_layout = QVBoxLayout(self)

        self._configure_section_frame()
        self._configure_section_layout()

    def build(self, actor_items: list[dict]) -> None:
        if self._current_actor_items == actor_items:
            return

        self._current_actor_items = actor_items
        actor_table_rows = self._build_actor_table_rows(actor_items)

        if self.actors_table_widget is None:
            self._build_actors_table_section(actor_table_rows)
            return

        self.actors_table_widget.update_rows(rows=actor_table_rows)

    def _configure_section_frame(self) -> None:
        self.setObjectName("section_actors")
        self.setStyleSheet(APP_THEME.bottom_border_qss())
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def _configure_section_layout(self) -> None:
        self.actors_section_layout.setContentsMargins(0, 0, 0, 0)
        self.actors_section_layout.setSpacing(0)

    def _build_actors_table_section(self, actor_table_rows: list[dict]) -> None:
        self.actors_title_widget = LabelValueWidget("Actors", parent=self)
        self.actors_table_widget = SimpleTableWidget(
            rows=actor_table_rows,
            cols=ACTOR_TABLE_COLUMN_KEYS,
            headers=ACTOR_TABLE_COLUMN_HEADERS,
            resize_modes=ACTOR_TABLE_COLUMN_RESIZE_MODES,
        )

        self.actors_section_layout.addWidget(self.actors_title_widget)
        self.actors_section_layout.addWidget(self.actors_table_widget)

    def _build_actor_table_rows(self, actor_items: list[dict]) -> list[dict]:
        actor_table_rows: list[dict] = []

        for actor_item in actor_items:
            actor_table_row = dict(actor_item)
            actor_table_row["thumb"] = pathlib.Path(
                actor_table_row.get("thumb", "")
            ).suffix
            actor_table_rows.append(actor_table_row)

        return actor_table_rows
