from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QSizePolicy,
    QVBoxLayout,
    QTableView,
    QTableWidget,
)

from src.widgets.simple_table_model import SimpleTableModel
from src.theme.theme import APP_THEME


class SimpleTableWidget(QTableWidget):
    def __init__(
        self,
        rows: list[dict],
        cols: list[str],
        headers: list[str],
        resize_modes: list[QHeaderView.ResizeMode],
    ) -> None:
        super().__init__()

        self.table: QTableView | None = None
        self.model: SimpleTableModel | None = None
        self.build(
            rows,
            cols,
            headers,
            resize_modes,
        )

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.apply_theme()

    def update_rows(
        self,
        rows: list[dict],
        headers: list[str] | None = None,
        cols: list[str] | None = None,
    ):

        if self.model is None:
            return
        nbr_rows = len(rows)
        self._update_table_height(nbr_rows)
        self.model.update_rows(rows=rows, headers=headers, cols=cols)
        self.table.resizeColumnsToContents()
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    def _update_table_height(self, nbr_rows: int) -> None:
        # 12px font; 17 * 2 close to manual 35
        line_height = self.table.fontMetrics().lineSpacing() * 2
        # print(f"_update_table_height: line_height:{line_height}")
        min_height = 2 * line_height
        max_height = (nbr_rows + 1) * line_height
        # if max_height > self._max_height:
        #     max_height = self._max_height

        if nbr_rows == 0:
            self.table.setMinimumHeight(0)
            self.table.setMaximumHeight(line_height)
            self.table.setRowHidden(0, True)
        else:
            self.table.setMinimumHeight(min_height)
            self.table.setMaximumHeight(max_height)
            self.table.setRowHidden(0, False)

    def build(
        self,
        rows: list[dict],
        cols: list[str],
        headers: list[str],
        resize_modes: list[QHeaderView.ResizeMode],
    ) -> None:

        self.table = QTableView()
        self.model = SimpleTableModel(rows, headers, cols)
        self.table.setModel(self.model)

        self.table.setAutoScroll(True)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.AscendingOrder)
        self.table.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))

        header = self.table.horizontalHeader()
        for index, resize_mode in enumerate(resize_modes):
            header.setSectionResizeMode(index, resize_mode)
        # prevent auto-stretch on last column
        header.setStretchLastSection(False)
        header.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))

        nbr_rows = len(rows)
        self._update_table_height(nbr_rows)

        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def apply_theme(self) -> None:
        if self.table is None:
            return

        self.table.setStyleSheet(APP_THEME.table_qss())
        self.table.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))

        header = self.table.horizontalHeader()
        header.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
