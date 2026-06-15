import math

from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt

from src.theme.theme import APP_THEME


class LabelAngledWidget(QtWidgets.QLabel):
    """
    A QLabel that supports rendering text at an angle.
    The widget automatically adjusts its size hint to accommodate the rotated text.
    """

    def __init__(self, text: str, angle: int = 0, parent=None):
        super().__init__(text, parent)
        self._angle = angle

    @property
    def angle(self) -> int:
        return self._angle

    @angle.setter
    def angle(self, value: int):
        if self._angle != value:
            self._angle = value
            self.updateGeometry()
            self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)

        # Center the coordinate system in the widget
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)

        # Calculate text bounding rect based on current font metrics
        fm = painter.fontMetrics()
        text_rect = fm.boundingRect(self.text())

        # Center the bounding rect around the origin (0, 0)
        text_rect.moveCenter(QtCore.QPoint(0, 0))

        # Use the current palette for the text color
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())

        painter.end()

    def _get_rotated_size(self, size: QtCore.QSize) -> QtCore.QSize:
        """Helper to calculate the bounding box of the widget after rotation."""
        w = size.width()
        h = size.height()
        rad = math.radians(self._angle)
        cos_a = abs(math.cos(rad))
        sin_a = abs(math.sin(rad))

        # Standard formula for rotated bounding box
        new_w = w * cos_a + h * sin_a
        new_h = w * sin_a + h * cos_a

        return QtCore.QSize(int(math.ceil(new_w)), int(math.ceil(new_h)))

    def minimumSizeHint(self) -> QtCore.QSize:
        return self._get_rotated_size(super().minimumSizeHint())

    def sizeHint(self) -> QtCore.QSize:
        return self._get_rotated_size(super().sizeHint())

    def apply_theme(self) -> None:
        """Applies the application theme to the widget."""
        self.setFont(QtGui.QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.setStyleSheet(APP_THEME.label_qss())
