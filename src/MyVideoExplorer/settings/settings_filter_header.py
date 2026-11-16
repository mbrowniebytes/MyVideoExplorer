from __future__ import annotations

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QMouseEvent, QPainter
from PySide6.QtWidgets import QHeaderView, QStyle, QStyleOptionHeader, QWidget


class SettingsFilterHeader(QHeaderView):
    """Header that paints and sorts grouped Media and Criteria columns."""

    groupedSortRequested = Signal(int, object)
    _groups = ((3, 4, "Media"), (5, 6, "Criteria"))

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setMinimumHeight(self.fontMetrics().height() * 2 + 4)

    def paintSection(self, painter: QPainter, rect: QRect, logical_index: int) -> None:
        option = QStyleOptionHeader()
        self.initStyleOption(option)
        option.rect = rect
        option.section = logical_index
        option.text = ""
        self.style().drawControl(QStyle.ControlElement.CE_Header, option, painter, self)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        group_by_first = {first: (last, title) for first, last, title in self._groups}
        grouped_columns = {
            column
            for first, last, _ in self._groups
            for column in range(first, last + 1)
        }
        column = 0
        while column < self.count():
            if self.isSectionHidden(column):
                column += 1
                continue
            group = group_by_first.get(column)
            if column in grouped_columns and group is None:
                column += 1
                continue

            last, title = group if group is not None else (column, "")
            if group is None:
                title = str(
                    self.model().headerData(
                        column, self.orientation(), Qt.ItemDataRole.DisplayRole
                    )
                    or ""
                )
            start = self.sectionViewportPosition(column)
            end = self.sectionViewportPosition(last) + self.sectionSize(last)
            rect = QRect(start, 0, end - start, self.height())
            text_rect = QRect(rect)
            text_rect.setTop(self.height() // 2)
            painter.setFont(self.font())
            painter.setPen(self.palette().color(self.foregroundRole()))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, title)

            if self.sortIndicatorSection() == column:
                option = QStyleOptionHeader()
                self.initStyleOption(option)
                option.section = column
                option.sortIndicator = (
                    QStyleOptionHeader.SortIndicator.SortDown
                    if self.sortIndicatorOrder() == Qt.SortOrder.DescendingOrder
                    else QStyleOptionHeader.SortIndicator.SortUp
                )
                mark_size = self.style().pixelMetric(
                    QStyle.PixelMetric.PM_HeaderMarkSize, option, self
                )
                option.rect = QRect(
                    rect.center().x() - mark_size // 2,
                    (self.height() // 2 - mark_size) // 2,
                    mark_size,
                    mark_size,
                )
                self.style().drawPrimitive(
                    QStyle.PrimitiveElement.PE_IndicatorHeaderArrow,
                    option,
                    painter,
                    self,
                )

            column = last + 1

    def mousePressEvent(self, event: QMouseEvent) -> None:
        x = event.position().toPoint().x()
        for first, last, _ in self._groups:
            start = self.sectionViewportPosition(first)
            end = self.sectionViewportPosition(last) + self.sectionSize(last)
            if start <= x < end:
                order = (
                    Qt.SortOrder.DescendingOrder
                    if self.sortIndicatorSection() == first
                    and self.sortIndicatorOrder() == Qt.SortOrder.AscendingOrder
                    else Qt.SortOrder.AscendingOrder
                )
                self.blockSignals(True)
                self.setSortIndicator(first, order)
                self.blockSignals(False)
                self.groupedSortRequested.emit(first, order)
                event.accept()
                return
        super().mousePressEvent(event)
