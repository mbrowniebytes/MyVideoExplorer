import math

from PySide6 import QtWidgets as Widgets, QtGui, QtCore
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont

from src.theme.theme import APP_THEME


class LabelAngledWidget(Widgets.QLabel):

    def __init__(self, text: str, angle: int = 0, *args):
        Widgets.QLabel.__init__(self, *args)

        self.setText(text)

        self.angle = angle

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        fm = QtGui.QFontMetrics(painter.font())

        text_rect = fm.boundingRect(self.text())

        if self.alignment() == Qt.AlignmentFlag.AlignTop:
            v_y = text_rect.height()
        else:
            v_y = self.height() / 2
        v_x = self.width() / 2
        painter.translate(v_x, v_y)

        painter.rotate(self.angle)

        h_x = -int(text_rect.width() / 2)
        h_y = int(text_rect.height() / 2)
        label_point = QPoint(h_x, h_y)

        painter.drawText(label_point, self.text())

        painter.end()

    def minimumSizeHint(self):
        size = Widgets.QLabel.minimumSizeHint(self)
        return QtCore.QSize(
            size.height()
            + math.ceil(size.height() * abs(math.cos(math.radians(self.angle)))),
            size.width()
            + math.ceil(size.width() * abs(math.sin(math.radians(self.angle)))),
        )

    def sizeHint(self):
        size = Widgets.QLabel.sizeHint(self)
        return QtCore.QSize(
            size.height()
            + math.ceil(size.height() * abs(math.cos(math.radians(self.angle)))),
            size.width()
            + math.ceil(size.width() * abs(math.sin(math.radians(self.angle)))),
        )

    def apply_theme(self) -> None:
        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.setStyleSheet(APP_THEME.label_qss())
