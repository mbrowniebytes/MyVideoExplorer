from __future__ import annotations


from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.str_util import StrUtil
from MyVideoExplorer.utils.ui_utils import UIUtils
from MyVideoExplorer.widgets.label_value_widget import LabelValueWidget

type MediaInfoField = tuple[str, object]
type MediaInfoFieldRow = list[MediaInfoField]
type MediaInfoFieldRows = list[MediaInfoFieldRow]


class MediaInfoCommonSection(QWidget, ThemableMixin):
    def __init__(self, str_util: StrUtil, log_util: LogUtil | None = None, parent=None):
        super().__init__(parent)
        self.log_util = log_util or LogUtil()
        self._ui_utils = UIUtils()
        self._current_view_mode = ""
        self._current_nfo = {}
        self.setObjectName("section_common")
        self.setStyleSheet(APP_THEME.bottom_border_qss())
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        self.str_util = str_util

    def apply_theme(self) -> None:
        super().apply_theme()
        self.setStyleSheet(APP_THEME.table_qss())
        self.setStyleSheet(APP_THEME.bottom_border_qss())

    def build(self, nfo: dict, view_mode: str) -> None:
        if self._current_nfo == nfo and self._current_view_mode == view_mode:
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
        self._ui_utils.clear_layout(self.layout)

        col_layout = QVBoxLayout()
        col_layout.setContentsMargins(0, 0, 0, 0)
        for row in top_fields:
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)
            for label, value in row:
                lvw = LabelValueWidget(
                    name=label, value=value, parent=self
                )
                row_layout.addWidget(lvw)
            col_layout.addLayout(row_layout)
        self.layout.addLayout(col_layout)

    # Removed _clear_layout in favor of UIUtils.clear_layout
