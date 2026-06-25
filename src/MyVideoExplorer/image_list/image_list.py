from __future__ import annotations

import pathlib

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.file_list.file_list import FileList
from MyVideoExplorer.image_list.image_list_view import ImageListView
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.utils.str_util import StrUtil
from MyVideoExplorer.widgets.base_widget import BaseWidget


class ImageList(BaseWidget):
    sig_wheel_step = Signal(object)
    sig_right_click = Signal(object)
    sig_double_click = Signal(object)
    sig_image_selected_intent = Signal(object)

    def __init__(
        self,
        file_util: FileUtil,
        nfo_parse_util: NfoParseUtil,
        str_util: StrUtil,
        image_list_view: ImageListView,
        file_list: FileList,
        log_util: LogUtil,
    ) -> None:
        super().__init__(log_util)
        self.nfo_parse_util = nfo_parse_util
        self.file_util = file_util
        self.str_util = str_util
        self.image_list = None
        self.images: list[str] = []
        self.selected_image_index = -1
        self.selected_image_path = ""
        self.image_list_view = image_list_view
        self.image_list_view.file_list = file_list
        self._signals_connected = False

    def set_selected_image(self, image_path: str) -> None:
        if not image_path:
            self._reset_image_state()
            self._clear_preview()
            self.clear_nfo()
            return

        if image_path == self.selected_image_path:
            return

        self._load_folder_images(image_path)

    def build(self):
        self.image_list = self.image_list_view.build()
        self._connect_internal_sigs()
        self.clear_nfo()
        return self.image_list

    def _handle_wheel_step(self, payload: SignalPayload) -> None:
        new_payload = SignalPayload(
            data=payload.data,
            sender=self.__class__.__name__,
            name="Wheel Step",
            description="Emitted when mouse wheel moves in ImageList.",
            flow=SignalFlow.COMPONENT_INTERACTION,
        )
        self.sig_wheel_step.emit(new_payload)
        self.log_util.debug(f"sig_wheel_step emitted with: {payload.data}")

    def _handle_right_click(self, payload: SignalPayload) -> None:
        new_payload = SignalPayload(
            data=None,
            sender=self.__class__.__name__,
            name="Right Click",
            description="Emitted when right click in ImageList.",
            flow=SignalFlow.COMPONENT_INTERACTION,
        )
        self.sig_right_click.emit(new_payload)
        self.log_util.debug("sig_right_click emitted")

    def _handle_double_click(self, payload: SignalPayload) -> None:
        new_payload = SignalPayload(
            data=None,
            sender=self.__class__.__name__,
            name="Double Click",
            description="Emitted when double click in ImageList.",
            flow=SignalFlow.COMPONENT_INTERACTION,
        )
        self.sig_double_click.emit(new_payload)
        self.log_util.debug("sig_double_click emitted")

    def _connect_internal_sigs(self):
        if self._signals_connected:
            return
        self.image_list_view.sig_wheel_step.connect(self._handle_wheel_step)
        self.image_list_view.sig_right_click.connect(self._handle_right_click)
        self.image_list_view.sig_double_click.connect(self._handle_double_click)
        self._signals_connected = True

    def refresh(self, folder_path: str | None) -> None:
        if self.property("current_folder") == folder_path:
            return
        self.setProperty("current_folder", folder_path)
        self.update_image_from_folder(folder_path or "")

    def request_next_image(self, step: int = 1) -> None:
        if not self.images:
            return

        current_index = self.selected_image_index
        if current_index < 0:
            current_index = 0

        nbr_images = len(self.images)
        new_index = 0 if current_index + step >= nbr_images else current_index + step

        image_path = self.images[new_index]
        if not image_path:
            return

        self.selected_image_index = new_index
        self.selected_image_path = image_path
        self.image_list_view.load_pixmap(image_path)
        payload = SignalPayload(
            data=image_path,
            sender=self.__class__.__name__,
            name="Image Selected Intent",
            description="Emitted when an image selection is intended.",
            flow=SignalFlow.USER_INPUT,
        )
        self.sig_image_selected_intent.emit(payload)
        self.log_util.debug(f"sig_image_selected_intent emitted for: {image_path}")

    def clear_nfo(self) -> None:
        self.image_list_view.clear_nfo()

    def build_nfo(self, folder_path: str) -> None:
        nfo = self.nfo_parse_util.parse_nfo_folder(folder_path)
        self.image_list_view.build_nfo(nfo)

    def _reset_image_state(self) -> None:
        self.images = []
        self.selected_image_index = -1
        self.selected_image_path = ""

    def _clear_preview(self) -> None:
        self.image_list_view.load_pixmap(None)

    def _load_folder_images(self, image_path: str) -> bool:
        if not image_path or not self.file_util.is_image_file(image_path):
            self._reset_image_state()
            self._clear_preview()
            self.clear_nfo()
            return False

        folder_path = str(pathlib.Path(image_path).parent)
        images, _poster_path = self.file_util.get_images_from_folder(folder_path)

        if not images:
            self._reset_image_state()
            self._clear_preview()
            self.clear_nfo()
            return False

        self.images = images
        if image_path in images:
            self.selected_image_index = images.index(image_path)
            self.selected_image_path = image_path
        else:
            self.selected_image_index = 0
            self.selected_image_path = images[0]

        self.image_list_view.load_pixmap(self.selected_image_path)
        self.build_nfo(folder_path)
        return True

    def update_image_from_item(self, image_path: str) -> None:
        # self.clear_nfo()
        self._load_folder_images(image_path)

    def update_image_from_folder(self, folder_path: str) -> None:
        # self.clear_nfo()

        if not folder_path:
            self._reset_image_state()
            self._clear_preview()
            return

        images, poster_path = self.file_util.get_images_from_folder(folder_path)
        self.images = images
        self.selected_image_index = -1
        self.selected_image_path = ""

        if not images:
            self._clear_preview()
            return

        selected_image = poster_path if poster_path in images else images[0]
        self.selected_image_path = selected_image
        self.selected_image_index = images.index(selected_image)
        self.image_list_view.load_pixmap(selected_image)

        self.build_nfo(folder_path)

    def apply_theme(self) -> None:
        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.setStyleSheet(APP_THEME.container_qss())
        self.image_list_view.apply_theme()
