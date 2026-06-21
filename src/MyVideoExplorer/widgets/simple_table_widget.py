from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QSizePolicy,
    QVBoxLayout,
    QTableView,
    QWidget,
)

from MyVideoExplorer.widgets.simple_table_model import SimpleTableModel
from MyVideoExplorer.theme.theme import APP_THEME


class SimpleTableWidget(QWidget):
    """A reusable widget that wraps a QTableView and its model for easy data display."""

    def __init__(
        self,
        rows: list[dict],
        cols: list[str],
        headers: list[str],
        resize_modes: list[QHeaderView.ResizeMode],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.table: QTableView
        self.model: SimpleTableModel
        self.build(
            rows,
            cols,
            headers,
            resize_modes,
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.apply_theme()

    def update_rows(
        self,
        rows: list[dict],
        headers: list[str] | None = None,
        cols: list[str] | None = None,
    ) -> None:
        """Updates the table data and adjusts the view accordingly."""
        if self.model is None or self.table is None:
            return

        self.model.update_rows(rows=rows, headers=headers, cols=cols)
        self._update_table_height(len(rows))
        self.table.resizeColumnsToContents()

    def _update_table_height(self, nbr_rows: int) -> None:
        """Calculates and sets the table height based on its content."""
        if self.table is None:
            return

        # 12px font; 17 * 2 close to manual 35
        line_height = self.table.fontMetrics().lineSpacing() * 2
        min_height = 2 * line_height
        max_height = (nbr_rows + 1) * line_height

        if nbr_rows == 0:
            self.table.setMinimumHeight(0)
            self.table.setMaximumHeight(line_height)
        else:
            self.table.setMinimumHeight(min_height)
            self.table.setMaximumHeight(max_height)

        # Safely handle the visibility of the first row
        if self.model and self.model.rowCount() > 0:
            self.table.setRowHidden(0, nbr_rows == 0)

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
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.table.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))

        header = self.table.horizontalHeader()
        for index, resize_mode in enumerate(resize_modes):
            header.setSectionResizeMode(index, resize_mode)
        # prevent auto-stretch on last column
        header.setStretchLastSection(False)
        header.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))

        nbr_rows = len(rows)
        self._update_table_height(nbr_rows)

        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def apply_theme(self) -> None:
        """Applies consistent styling and fonts from the application theme."""
        if self.table is None:
            return

        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.table.setStyleSheet(APP_THEME.table_qss())
        self.table.setFont(font)

        header = self.table.horizontalHeader()
        header.setFont(font)
