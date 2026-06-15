from __future__ import annotations


from PySide6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout

from src.theme.theme import APP_THEME
from src.utils.str_util import StrUtil
from src.widgets.label_value_widget import LabelValueWidget


type MediaInfoField = tuple[str, object]
type MediaInfoFieldRow = list[MediaInfoField]
type MediaInfoFieldRows = list[MediaInfoFieldRow]


class MediaInfoCommonSection(QFrame):
    def __init__(self, str_util: StrUtil, parent=None):
        super().__init__(parent)
        self.setObjectName("section_common")
        self.setStyleSheet(APP_THEME.bottom_border_qss())
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        self.str_util = str_util

    def build(self, nfo: dict, view_mode: str) -> None:
        if (
            hasattr(self, "_current_nfo")
            and self._current_nfo == nfo
            and hasattr(self, "_current_view_mode")
            and self._current_view_mode == view_mode
        ):
            return

        self._current_nfo = nfo
        self._current_view_mode = view_mode

        if view_mode == "image_list":
            top_fields = [
                [
                    ("Year", nfo.get("year", "")),
                    ("Score", nfo.get("rating", "")),
                    ("Rating", nfo.get("mpaa", "")),
                    ("Runtime", nfo.get("runtime", "")),
                ],
                [("Tagline", nfo.get("tagline", ""))],
                [
                    ("Directors", self.str_util.join_strings(nfo.get("directors", []))),
                    ("Genres", self.str_util.join_strings(nfo.get("genres", []))),
                ],
            ]
        else:
            top_fields = [
                [("Title", nfo.get("title", ""))],
                [
                    ("Year", nfo.get("year", "")),
                    ("Score", nfo.get("rating", "")),
                    ("Rating", nfo.get("mpaa", "")),
                    ("Runtime", nfo.get("runtime", "")),
                ],
                [("Tagline", nfo.get("tagline", ""))],
                [
                    ("Directors", self.str_util.join_strings(nfo.get("directors", []))),
                    ("Genres", self.str_util.join_strings(nfo.get("genres", []))),
                ],
                [("Set", nfo.get("set", "")), ("Source", nfo.get("source", ""))],
            ]

        # Use existing widgets if possible
        existing_widgets = []
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item.layout():
                for j in range(item.layout().count()):
                    w = item.layout().itemAt(j).widget()
                    if isinstance(w, LabelValueWidget):
                        existing_widgets.append(w)

        # Flatten top_fields for easier matching
        flat_fields = []
        for row in top_fields:
            for label, value in row:
                flat_fields.append((label, value))

        if len(existing_widgets) == len(flat_fields):
            # Same structure, just update values
            for widget, (label, value) in zip(existing_widgets, flat_fields):
                widget.set_value(value)
            return

        # Structure changed, rebuild
        # Clear existing rows
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.layout():
                self._clear_layout(item.layout())
                item.layout().deleteLater()
            elif item.widget():
                item.widget().deleteLater()

        for row in top_fields:
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)
            for label, value in row:
                row_layout.addWidget(LabelValueWidget(label, value))
            self.layout.addLayout(row_layout)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
