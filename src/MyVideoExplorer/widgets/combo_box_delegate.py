from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QSize, Qt
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem

if TYPE_CHECKING:
    from collections.abc import Iterable

    from PySide6.QtCore import QObject


class GroupedComboBoxDelegate(QStyledItemDelegate):
    """
    Custom delegate for QComboBox dropdowns that provides extra height for group headers.

    Group headers are non-selectable items that separate sections in the dropdown.
    This delegate makes them slightly taller to give visual breathing room.
    """

    def __init__(
        self,
        group_headers: Iterable[str] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._group_headers: set[str] = set(group_headers or [])

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        model_index: QModelIndex | QPersistentModelIndex,
    ) -> QSize:
        """Return a slightly taller height for group headers."""
        data = model_index.data(Qt.ItemDataRole.DisplayRole)
        base = super().sizeHint(option, model_index)
        if data is not None and str(data) in self._group_headers:
            return QSize(base.width(), base.height() + 4)
        return base
