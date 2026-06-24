from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.app.app_signals_model import SignalPayload
from MyVideoExplorer.folder_list.folder_list_view import FolderListView
from MyVideoExplorer.settings.settings import Settings
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.base_widget import BaseWidget

_EMPTY_STATE_NO_MEDIA_FOLDERS = (
    "No media folders configured.\nOpen Settings (Gear) → Media and add a media folder."
)


class FolderList(BaseWidget):
    sig_folder_selected_intent = Signal(object)

    def __init__(
        self, file_util: FileUtil, settings: Settings, log_util: LogUtil, parent=None
    ) -> None:
        super().__init__(log_util)
        self.help_icon = QLabel()
        self.title_label = QLabel()
        self.folder_list_view = FolderListView(log_util=self.log_util)
        self.file_util = file_util
        self.settings = settings
        self._signals_connected = False
        self._container = QWidget()

    def build(self) -> QWidget:
        self._container = self._build_container()
        layout = QVBoxLayout(self._container)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("Folders")
        self.title_label.setStyleSheet(APP_THEME.label_qss())

        self.help_icon = QLabel("?")
        self.help_icon.setToolTip(
            "Folder List Usage:\n"
            "- Click a folder to view its contents\n"
            "- Use 'Add Media Folder' in settings to add more roots\n"
            "- Use the folder picker to browse other directories"
        )
        self.help_icon.setStyleSheet(APP_THEME.help_icon_label_qss())
        self.help_icon.setFixedSize(16, 16)
        self.help_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.help_icon)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        layout.addWidget(self.folder_list_view)
        self.folder_list_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        if not self._has_valid_media_folders():
            self.folder_list_view.show_empty_state(
                message=_EMPTY_STATE_NO_MEDIA_FOLDERS
            )
        else:
            self.folder_list_view.show_loading_state()

        self.connect_sigs()
        return self._container

    def _build_container(self) -> QWidget:
        container = QWidget()
        container.setObjectName("folderListContainer")
        container.setMinimumWidth(200)
        container.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        container.setStyleSheet(APP_THEME.container_qss())
        return container

    def refresh(self, folder_path: str, force: bool = False) -> None:
        # if not folder_path:
        #     self.folder_view.show_empty_state()
        #     return

        # If there are no configured media folders or none are valid,
        # show a helpful instruction to add media folders in Settings.
        if not self._has_valid_media_folders():
            self.folder_list_view.show_empty_state(
                message=_EMPTY_STATE_NO_MEDIA_FOLDERS
            )
            return

        if not force and self.folder_list_view.count() > 0:
            # If we already have items, just try to select the folder
            # This avoids full refresh if the folder is already in the list
            found = False
            for row in range(self.folder_list_view.count()):
                item = self.folder_list_view.item(row)
                if item and item.data(Qt.ItemDataRole.UserRole) == folder_path:
                    self.folder_list_view.setCurrentRow(row)
                    self.folder_list_view.scrollToItem(item)
                    found = True
                    break
            if found:
                return

        self.folder_list_view.show_loading_state()

        # folder_Filter.apply_filters also loading
        # QTimer.singleShot(250, lambda: self.update_folder_list_by_path(folder_path))

    def _handle_folder_selected_intent(self, payload: SignalPayload) -> None:
        self.sig_folder_selected_intent.emit(payload)
        self.log_util.debug(f"sig_folder_selected_intent emitted for: {payload.data}")

    def connect_sigs(self):
        if self._signals_connected:
            return
        self.folder_list_view.sig_folder_selected.connect(
            self._handle_folder_selected_intent
        )
        self._signals_connected = True

    def set_selected_folder(self, folder_path: str) -> None:
        self.folder_list_view.set_selected_folder(folder_path)
        # Important: Don't call refresh here as it might trigger a full rebuild

    def show_loading_state(self, folders: list[str] = None) -> None:
        self.folder_list_view.show_loading_state(folders)

    def select_next_folder(self, step: int = 1) -> None:
        self.folder_list_view.select_next_folder(step)

    def refresh_icons(self) -> None:
        self.folder_list_view.refresh_icons(self._get_icon_for_path)

    def _has_valid_media_folders(self) -> bool:
        """Return True if settings contains at least one existing media folder path."""
        if not self.settings:
            return False
        import os

        for config in self.settings.settings_data_model.folder_configs:
            p = config.get("path", "")
            if p and os.path.isdir(p):
                return True
        return False

    # used by tests
    def update_folder_list_by_path(
        self, path: str, on_complete: callable = None
    ) -> None:
        """Loads folders from a path and updates the view."""
        self.folder_list_view.show_loading_state([path])
        self.file_util.get_files_from_path_async(
            path,
            on_complete=lambda items: self.populate_view(
                items, on_complete=on_complete
            ),
        )

    # used by tests
    def update_folder_list_by_items(self, items: list[FileUtilModel]) -> None:
        """Updates the view with a list of items."""
        self.populate_view(items)

    def apply_theme(self) -> None:
        # super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)

        self._container.setFont(font)

        self.title_label.setStyleSheet(APP_THEME.label_qss())
        self.help_icon.setStyleSheet(
            APP_THEME.label_qss("small")
            + "; border: 1px solid palette(text); border-radius: 8px;"
        )

        # breaks app theme apply
        # self.folder_list_view.setStyleSheet(APP_THEME.get_list_qss())

    def populate_view(self, items: list[FileUtilModel], on_complete: callable = None):
        """Sorts and populates the FolderListView."""
        self.folder_list_view.populate_view(
            items, get_icon_func=self._get_icon_for_path, on_complete=on_complete
        )

    def _get_icon_for_path(self, path: str) -> str:
        if not self.settings:
            return "fa5s.folder"

        norm_path = path.lower()
        for config in self.settings.settings_data_model.folder_configs:
            cfg_path = config.get("path", "")
            if not cfg_path:
                continue
            cfg_path = Path(cfg_path).as_posix().lower()
            # print(f"_get_icon_for_path: cfg_path: {cfg_path}, norm_path: {norm_path}")
            if norm_path.startswith(cfg_path):
                return config.get("icon", "fa5s.folder")

        return "fa5s.folder"
