from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QVBoxLayout, QWidget

from MyVideoExplorer.image_list.image_label import ImageLabel
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.ui_utils import UIUtils

_NO_IMAGE_FOUND = """
    No image found.\n
    Select a folder by Mouse Wheel over this area\n
    or by Selecting a folder in the Folder list to the left.
"""


class ImagePreviewWidget(QWidget, ThemableMixin):
    """
    Widget for previewing an image with automatic scaling and delayed rendering.
    """

    wheel_step = Signal(object)
    context_menu_requested = Signal(object)
    double_click_requested = Signal(object)

    def __init__(self, log_util: LogUtil, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.log_util = log_util
        self._ui_utils = UIUtils()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.apply_scaled_pixmap)
        self._pixmap: QPixmap | None = None
        self._loading_state_text = "Loading..."

        self.image_label = ImageLabel(log_util, _NO_IMAGE_FOUND)
        self.image_label.wheel_step.connect(self.wheel_step.emit)
        self.image_label.context_menu_requested.connect(
            self.context_menu_requested.emit
        )
        self.image_label.double_click_requested.connect(
            self.double_click_requested.emit
        )

        layout = self._ui_utils.apply_compact_layout(self, QVBoxLayout)
        layout.addWidget(self.image_label)

    def load_pixmap(self, image_path: str | None) -> None:
        try:
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
        except Exception as e:
            if self.log_util:
                self.log_util.error(f"Error in load_pixmap: {e!s}")
            raise

    def _reset_preview(self) -> None:
        self._pixmap = None
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText(_NO_IMAGE_FOUND)

    def show_loading_state(self, message: str = "") -> None:
        self._pixmap = None
        self.image_label.setPixmap(QPixmap())
        text = self._loading_state_text
        if message:
            text += f"\n\n{message}"
        self.image_label.setText(text)

    def show_empty_state(self, message: str = "") -> None:
        self._pixmap = None
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText(message or _NO_IMAGE_FOUND)

    def resize_pixmap(self) -> None:
        self.image_label.clear()
        self.timer.stop()
        self.timer.start(100)

    def apply_scaled_pixmap(self) -> None:
        try:
            self.timer.stop()
            if not self._pixmap or self._pixmap.isNull():
                self.image_label.clear()
                self.image_label.setText(_NO_IMAGE_FOUND)
                return

            target_size = self.image_label.size()
            if target_size.width() <= 0 or target_size.height() <= 0:
                return

            scaled = self._pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
        except Exception as e:
            if self.log_util:
                self.log_util.error(f"Error in apply_scaled_pixmap: {e!s}")
            raise

    def apply_theme(self) -> None:
        super().apply_theme()
