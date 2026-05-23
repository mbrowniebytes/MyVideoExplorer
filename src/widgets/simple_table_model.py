from __future__ import annotations

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex


class SimpleTableModel(QAbstractTableModel):
    """A flexible table model for displaying data tables"""

    def __init__(self, rows: list[dict], headers: list[str], cols: list[str]):
        super().__init__()
        self._rows = rows
        self._headers = headers  # human-readable column labels
        self._cols = cols  # keys to access dict values

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | None:
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        # Handle display role only (no icons/links in tables yet)
        if role == Qt.DisplayRole:
            key = self._cols[col]
            value = self._rows[row].get(key, "")

            return str(value) if value is not None else ""

        return None

    def update_rows(
        self,
        rows: list[dict],
        headers: list[str] | None = None,
        cols: list[str] | None = None,
    ) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        if headers is not None:
            self._headers = headers
        if cols is not None:
            self._cols = cols
        self.endResetModel()

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        # Sort using the dict key (not header label)
        key_field = self._cols[column]

        def key_func(row_dict):
            val = row_dict.get(key_field, "")
            if isinstance(val, int) or isinstance(val, float):
                return val
            # elif isinstance(val, str) and val.isnumeric():
            #     return float(val)
            else:
                return str(val).lower()

        self.beginResetModel()
        try:
            self._rows.sort(
                key=key_func, reverse=(order == Qt.SortOrder.DescendingOrder)
            )
        except Exception as e:
            print(
                f"SimpleTableModel: sort failed for column {column}, key_field={key_field}: {e}"
            )
        self.endResetModel()

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.DisplayRole,
    ) -> str | None:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None
