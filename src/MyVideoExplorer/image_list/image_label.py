from PySide6.QtCore import Qt, Signal, QRect
from MyVideoExplorer.app.app_signals_model import SignalPayload, SignalFlow
from PySide6.QtGui import QFont, QPainter, QPen, QColor
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget
from MyVideoExplorer.utils.log_util import LogUtil

from MyVideoExplorer.theme.theme import APP_THEME


class ImageLabel(QLabel):
    sig_wheel_step = Signal(object)
    sig_right_click = Signal(object)
    sig_double_click = Signal(object)

    def __init__(self, log_util: LogUtil, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.log_util = log_util

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
        payload = SignalPayload(
            data=step,
            sender=self.__class__.__name__,
            name="Wheel Step",
            description="Emitted when mouse wheel moves in ImageLabel.",
            flow=SignalFlow.USER_INPUT,
        )
        self.sig_wheel_step.emit(payload)
        event.accept()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.RightButton:
            payload = SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Right Click",
                description="Emitted when right click in ImageLabel.",
                flow=SignalFlow.USER_INPUT,
            )
            self.sig_right_click.emit(payload)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            payload = SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Double Click",
                description="Emitted when double click in ImageLabel.",
                flow=SignalFlow.USER_INPUT,
            )
            self.sig_double_click.emit(payload)
            event.accept()
            return

        super().mouseDoubleClickEvent(event)

    def apply_theme(self) -> None:
        if not APP_THEME.is_refreshing:
            APP_THEME.refresh_theme(self)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.setProperty("highlight", "true")
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.setProperty("highlight", "false")
        self.update()

    def paintEvent(self, event):
        try:
            super().paintEvent(event)
            if self.property("highlight") == "true" and self.pixmap() and not self.pixmap().isNull():
                painter = QPainter(self)
                pixmap = self.pixmap()
                pixmap_size = pixmap.size()
                label_size = self.size()

                x = (label_size.width() - pixmap_size.width()) // 2
                y = (label_size.height() - pixmap_size.height()) // 2
                rect = QRect(x, y, pixmap_size.width(), pixmap_size.height())

                pen = QPen(QColor(APP_THEME.config.color_interaction_pixmap), APP_THEME.config.size_interaction_pixmap)
                painter.setPen(pen)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.drawRoundedRect(
                    rect,
                    APP_THEME.config.size_border_radius_standard,
                    APP_THEME.config.size_border_radius_standard
                )
        except Exception as e:
            if self.log_util:
                self.log_util.error(f"Error in paintEvent: {str(e)}")
            raise
