from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QPersistentModelIndex


class SimpleTableModel(QAbstractTableModel):
    """A flexible table model for displaying data tables"""

    def __init__(self, rows: list[dict[str, Any]], headers: list[str], cols: list[str]) -> None:
        super().__init__()
        self._rows: list[dict[str, Any]] = rows
        self._headers = headers  # human-readable column labels
        self._cols = cols  # keys to access dict values

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._headers)

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = 0) -> Any:
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        key = self._cols[col]
        value = self._rows[row].get(key)

        # Qt roles - use type: ignore for Qt attributes that mypy may not recognize
        if role == Qt.DisplayRole:  # type: ignore[attr-defined]
            return str(value) if value is not None else ""

        if role == Qt.TextAlignmentRole:  # type: ignore[attr-defined]
            # Right-align numbers for better readability
            if isinstance(value, (int, float)):
                return (Qt.AlignRight | Qt.AlignVCenter)  # type: ignore[attr-defined]
            return (Qt.AlignLeft | Qt.AlignVCenter)  # type: ignore[attr-defined]

        return None

    def update_rows(
        self,
        rows: list[dict[str, Any]],
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

    def sort(self, column: int, order: int = Qt.AscendingOrder):  # type: ignore[attr-defined]
        # Sort using the dict key (not header label)
        key_field = self._cols[column]

        def key_func(row_dict: dict[str, Any]) -> object:
            val = row_dict.get(key_field)
            if val is None:
                return ""
            if isinstance(val, (int, float)):
                return val
            return str(val).lower()

        self.layoutAboutToBeChanged.emit()
        try:
            self._rows.sort(key=key_func, reverse=(order == Qt.DescendingOrder))  # type: ignore[attr-defined]
        except Exception as e:
            print(f"SimpleTableModel: sort failed for column {column}, key_field={key_field}: {e}")
        self.layoutChanged.emit()

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = 0,
    ) -> object | None:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:  # type: ignore[attr-defined]
            return self._headers[section]
        return None
