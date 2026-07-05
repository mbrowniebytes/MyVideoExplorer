from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.image_list.image_title_widget import ImageTitleWidget
from MyVideoExplorer.utils.log_util import LogUtil

if TYPE_CHECKING:
    from MyVideoExplorer.file_list.file_list import FileList

from MyVideoExplorer.image_list.image_preview_widget import ImagePreviewWidget
from MyVideoExplorer.media_info_side.media_info_side_view import MediaInfoSideView
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.utils.str_util import StrUtil
from MyVideoExplorer.utils.ui_utils import UIUtils


class ImageListView(QWidget, ThemableMixin):
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
        log_util: LogUtil,
    ) -> None:
        super().__init__()
        self.log_util = log_util
        self.str_util = str_util
        self.media_info_side_view = media_info_side_view
        self.file_list = file_list
        self._ui_utils = UIUtils()

        self.title_widget = ImageTitleWidget(log_util)
        self.preview_widget = ImagePreviewWidget(log_util)
        self.plot_text = self.media_info_side_view.get_plot_section().get_plot_text()
        self._loading_state_text = "Loading..."

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

        self.content_container = QWidget()
        self.content_container.setStyleSheet(APP_THEME.container_qss())
        self.content_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        main_layout = self._ui_utils.apply_compact_layout(self.content_container, QVBoxLayout)

        title_and_preview_widget = QWidget()
        title_and_preview_layout = self._ui_utils.apply_compact_layout(
            title_and_preview_widget, QVBoxLayout
        )
        title_and_preview_layout.addWidget(self.title_widget)
        title_and_preview_layout.addWidget(self.preview_widget)

        top_content_widget = QWidget()
        top_content_layout = self._ui_utils.apply_compact_layout(top_content_widget, QHBoxLayout)
        top_content_layout.addWidget(title_and_preview_widget, 2)
        top_content_layout.addWidget(self.media_info_side_view)

        main_layout.addWidget(top_content_widget)
        main_layout.addWidget(self.file_list.build())
        main_layout.addWidget(self.plot_text)

        root_layout = self._ui_utils.apply_compact_layout(self, QVBoxLayout)
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

    def show_loading_state(self, message: str = "") -> None:
        if self.preview_widget:
            self.preview_widget.show_loading_state(message)

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
        # super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.setFont(font)

        self.title_widget.apply_theme()
        self.preview_widget.apply_theme()

        self.plot_text.setFont(font)
        self.plot_text.document().setDefaultFont(font)

        self.file_list.apply_theme()

        self.media_info_side_view.apply_theme()
