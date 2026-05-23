import pathlib
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHeaderView, QSizePolicy
from src.theme.theme import APP_THEME
from src.widgets.simple_table_widget import SimpleTableWidget
from src.widgets.label_value_widget import LabelValueWidget


class MediaInfoActorsSection(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("section_actors")
        self.setStyleSheet(APP_THEME.bottom_border_qss())
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def build(self, actors: list[dict]) -> None:
        if hasattr(self, "_current_actors") and self._current_actors == actors:
            return
        self._current_actors = actors

        normalized_actors = self._normalize_actor_thumbs(actors)

        # Try to find existing Table
        existing_table = None
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if isinstance(w, SimpleTableWidget):
                existing_table = w
                break

        if existing_table:
            existing_table.update_rows(rows=normalized_actors)
        else:
            while self.layout.count():
                item = self.layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self._clear_layout(item.layout())

            self.layout.addWidget(LabelValueWidget("Actors"))
            self.layout.addWidget(
                SimpleTableWidget(
                    rows=normalized_actors,
                    cols=["order", "name", "role", "thumb"],
                    headers=["#", "Name", "Role", "Thumb"],
                    resize_modes=[
                        QHeaderView.ResizeMode.ResizeToContents,
                        QHeaderView.ResizeMode.Stretch,
                        QHeaderView.ResizeMode.Stretch,
                        QHeaderView.ResizeMode.ResizeToContents,
                    ],
                )
            )

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _normalize_actor_thumbs(self, actors: list[dict]) -> list[dict]:
        normalized_actors = []
        for actor in actors:
            actor_row = dict(actor)
            actor_row["thumb"] = pathlib.Path(actor_row.get("thumb", "")).suffix
            normalized_actors.append(actor_row)
        return normalized_actors
