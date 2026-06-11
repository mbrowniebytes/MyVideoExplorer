from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from src.app.app_signals_model import SignalPayload, SignalFlow
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
)

from src.image_list.image_title_widget import ImageTitleWidget

if TYPE_CHECKING:
    from src.file_list.file_list import FileList

from src.image_list.image_preview_widget import ImagePreviewWidget
from src.media_info_side.media_info_side_view import MediaInfoSideView
from src.theme.theme import APP_THEME
from src.utils.str_util import StrUtil
from src.widgets.base_widget import BaseWidget


class ImageListView(BaseWidget):
    """
    View for displaying an image and its related metadata.
    """

    sig_wheel_step = Signal(object)
    sig_right_click = Signal(object)
    sig_double_click = Signal(object)

    def __init__(
        self,
        str_util: StrUtil,
        media_info_side_view: MediaInfoSideView,
        file_list: FileList,
        log_util,
    ) -> None:
        super().__init__(log_util)
        self.str_util = str_util
        self.media_info_side_view = media_info_side_view
        self.file_list = file_list

        self.title_widget = ImageTitleWidget(log_util)
        self.preview_widget = ImagePreviewWidget(log_util)
        self.plot_text = self.media_info_side_view.get_plot_section().get_plot_text()

    def build(self) -> ImageListView:
        """
        Builds the UI components of the view.
        """
        self._build_ui()
        return self

    def _handle_wheel_step(self, payload: SignalPayload) -> None:
        step = payload.data
        new_payload = SignalPayload(
            data=step,
            sender=self.__class__.__name__,
            name="Wheel Step",
            description="Emitted when mouse wheel moves in ImageListView.",
            flow=SignalFlow.USER_INPUT,
        )
        self.sig_wheel_step.emit(new_payload)
        self.log_util.debug(f"sig_wheel_step emitted with: {step}")

    def _handle_right_click(self, payload: SignalPayload) -> None:
        new_payload = SignalPayload(
            data=None,
            sender=self.__class__.__name__,
            name="Right Click",
            description="Emitted when right click in ImageListView.",
            flow=SignalFlow.USER_INPUT,
        )
        self.sig_right_click.emit(new_payload)
        self.log_util.debug("sig_right_click emitted")

    def _handle_double_click(self, payload: SignalPayload) -> None:
        new_payload = SignalPayload(
            data=None,
            sender=self.__class__.__name__,
            name="Double Click",
            description="Emitted when double click in ImageListView.",
            flow=SignalFlow.USER_INPUT,
        )
        self.sig_double_click.emit(new_payload)
        self.log_util.debug("sig_double_click emitted")

    def _build_ui(self) -> None:
        self.preview_widget.sig_wheel_step.connect(self._handle_wheel_step)
        self.preview_widget.sig_right_click.connect(self._handle_right_click)
        self.preview_widget.sig_double_click.connect(self._handle_double_click)

        self.content_container = BaseWidget()
        self.content_container.setStyleSheet(APP_THEME.container_qss())
        self.content_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        main_layout = self.content_container.set_compact_layout(QVBoxLayout)
        main_layout.addWidget(self.title_widget)

        image_content_widget = BaseWidget()
        image_content_layout = image_content_widget.set_compact_layout(QHBoxLayout)
        image_content_layout.addWidget(self.preview_widget, 2)
        image_content_layout.addWidget(self.media_info_side_view)

        main_layout.addWidget(image_content_widget)
        main_layout.addWidget(self.file_list.build())
        main_layout.addWidget(self.plot_text)

        root_layout = self.set_compact_layout(QVBoxLayout)
        root_layout.addWidget(self.content_container, 0)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setMinimumSize(480, 300)

    def build_nfo(self, nfo: dict | None) -> None:
        if nfo is not None:
            self.media_info_side_view.build_nfo(nfo)
        self.preview_widget.resize_pixmap()

    def clear_nfo(self) -> None:
        self.media_info_side_view.clear_nfo()

    def resize_pixmap(self) -> None:
        if self.preview_widget:
            self.preview_widget.resize_pixmap()

    def load_pixmap(self, image_path: str | None) -> None:
        if self.preview_widget is None:
            return

        if image_path is None:
            self.title_widget.update_title("")
            self.preview_widget.load_pixmap(None)
            return

        media_folder = pathlib.Path(image_path).parent.name
        self.title_widget.update_title(media_folder)
        self.preview_widget.load_pixmap(image_path)

    def apply_theme(self) -> None:
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.setStyleSheet(APP_THEME.container_qss())
        self.setFont(font)

        self.title_widget.apply_theme()
        self.preview_widget.apply_theme()

        self.plot_text.setFont(font)
        self.plot_text.document().setDefaultFont(font)

        self.file_list.apply_theme()

        self.media_info_side_view.apply_theme()
