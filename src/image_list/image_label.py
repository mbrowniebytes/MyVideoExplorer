from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget

from src.theme.theme import APP_THEME


class ImageLabel(QLabel):
    sig_wheel_step = Signal(int)
    sig_right_click = Signal()
    sig_double_click = Signal()

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)

        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(APP_THEME.label_qss())
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def wheelEvent(self, event) -> None:
        delta_y = event.angleDelta().y()
        if delta_y == 0:
            super().wheelEvent(event)
            return

        step = 1 if delta_y < 0 else -1
        self.sig_wheel_step.emit(step)
        event.accept()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.RightButton:
            self.sig_right_click.emit()
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.sig_double_click.emit()
            event.accept()
            return

        super().mouseDoubleClickEvent(event)

    def apply_theme(self) -> None:
        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.setStyleSheet(APP_THEME.label_qss())
