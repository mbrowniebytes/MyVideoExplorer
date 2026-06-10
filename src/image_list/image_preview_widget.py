from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QVBoxLayout

from src.image_list.image_label import ImageLabel
from src.theme.theme import APP_THEME
from src.utils.log_util import LogUtil
from src.widgets.base_widget import BaseWidget

_NO_IMAGE_FOUND = """
    No image found.\n
    Select a folder by Mouse Wheel over this area\n
    or by Selecting a folder in the Folder list to the left.
"""


class ImagePreviewWidget(BaseWidget):
    """
    Widget for previewing an image with automatic scaling and delayed rendering.
    """

    sig_wheel_step = Signal(int)
    sig_right_click = Signal()
    sig_double_click = Signal()

    def __init__(self, log_util:LogUtil) -> None:
        super().__init__(log_util)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.apply_scaled_pixmap)
        self._pixmap: QPixmap | None = None

        self.image_label = ImageLabel(_NO_IMAGE_FOUND)
        self.image_label.sig_wheel_step.connect(self.sig_wheel_step.emit)
        self.image_label.sig_right_click.connect(self.sig_right_click.emit)
        self.image_label.sig_double_click.connect(self.sig_double_click.emit)

        layout = self.set_compact_layout(QVBoxLayout)
        layout.addWidget(self.image_label)

    def load_pixmap(self, image_path: str | None) -> None:
        if image_path is None:
            self._reset_preview()
            return

        self._pixmap = QPixmap(image_path)
        if self._pixmap.isNull():
            self._pixmap = None
            self.image_label.setStyleSheet(APP_THEME.label_qss())
            self.image_label.setText(_NO_IMAGE_FOUND)
            return

        self.image_label.setStyleSheet(APP_THEME.label_qss())
        self.image_label.setText("")
        self.apply_scaled_pixmap()

    def _reset_preview(self) -> None:
        self._pixmap = None
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText(_NO_IMAGE_FOUND)

    def resize_pixmap(self) -> None:
        self.image_label.clear()
        self.timer.stop()
        self.timer.start(100)

    def apply_scaled_pixmap(self) -> None:
        self.timer.stop()
        if not self._pixmap or self._pixmap.isNull():
            self.image_label.clear()
            self.image_label.setText(_NO_IMAGE_FOUND)
            return

        target_size = self.image_label.size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return

        scaled = self._pixmap.scaled(
            target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    def apply_theme(self) -> None:
        self.image_label.setStyleSheet(APP_THEME.label_qss())
        self.image_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
