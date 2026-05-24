from __future__ import annotations

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex


class SimpleTableModel(QAbstractTableModel):
    """A flexible table model for displaying data tables"""

    def __init__(self, rows: list[dict], headers: list[str], cols: list[str]):
        super().__init__()
        self._rows = rows
        self._headers = headers  # human-readable column labels
        self._cols = cols  # keys to access dict values

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> object | None:
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        key = self._cols[col]
        value = self._rows[row].get(key)

        if role == Qt.DisplayRole:
            return str(value) if value is not None else ""

        if role == Qt.TextAlignmentRole:
            # Right-align numbers for better readability
            if isinstance(value, (int, float)):
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

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
            val = row_dict.get(key_field)
            if val is None:
                return ""
            if isinstance(val, (int, float)):
                return val
            return str(val).lower()

        self.layoutAboutToBeChanged.emit()
        try:
            self._rows.sort(
                key=key_func, reverse=(order == Qt.SortOrder.DescendingOrder)
            )
        except Exception as e:
            print(
                f"SimpleTableModel: sort failed for column {column}, key_field={key_field}: {e}"
            )
        self.layoutChanged.emit()

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.DisplayRole,
    ) -> str | None:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None
