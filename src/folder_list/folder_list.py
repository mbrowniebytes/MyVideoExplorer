from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.folder_list.folder_list_view import FolderListView
from src.theme.theme import APP_THEME
from src.utils.file_util import FileUtil
from src.utils.file_util_model import FileUtilModel
from src.widgets.base_widget import BaseWidget

_EMPTY_STATE_NO_MEDIA_FOLDERS = (
    "No media folders configured.\nOpen Settings (Gear) → Media and add a media folder."
)




class FolderList(BaseWidget):
    sig_folder_selected_intent = Signal(str)

    def __init__(self, file_util: FileUtil, settings, log_util) -> None:
        super().__init__(log_util)
        self.folder_view = FolderListView()
        self.file_util = file_util
        self.settings = settings
        self._signals_connected = False
        self._container = QWidget()

    def build(self):
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
        self.help_icon.setStyleSheet(
            APP_THEME.help_icon_label_qss()
        )
        self.help_icon.setFixedSize(16, 16)
        self.help_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.help_icon)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        layout.addWidget(self.folder_view)
        self.folder_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.refresh("")

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
            self.folder_view.show_empty_state(message=_EMPTY_STATE_NO_MEDIA_FOLDERS)
            return

        if not force and self.folder_view.count() > 0:
            # If we already have items, just try to select the folder
            # This avoids full refresh if the folder is already in the list
            found = False
            for row in range(self.folder_view.count()):
                item = self.folder_view.item(row)
                if item and item.data(Qt.ItemDataRole.UserRole) == folder_path:
                    self.folder_view.setCurrentRow(row)
                    self.folder_view.scrollToItem(item)
                    found = True
                    break
            if found:
                return

        self.folder_view.show_loading_state()
        QTimer.singleShot(0, lambda: self.update_folder_list_by_path(folder_path))

    def _handle_folder_selected_intent(self, folder_path: str) -> None:
        self.sig_folder_selected_intent.emit(folder_path)
        self.log_util.debug(f"sig_folder_selected_intent emitted for: {folder_path}")

    def connect_sigs(self):
        if self._signals_connected:
            return
        self.folder_view.sig_folder_selected.connect(
            self._handle_folder_selected_intent
        )
        self._signals_connected = True

    def set_selected_folder(self, folder_path: str) -> None:
        self.folder_view.set_selected_folder(folder_path)
        # Important: Don't call refresh here as it might trigger a full rebuild

    def select_next_folder(self, step: int = 1) -> None:
        self.folder_view.select_next_folder(step)

    def refresh_icons(self) -> None:
        self.folder_view.refresh_icons(self._get_icon_for_path)

    def _get_icon_for_path(self, path: str) -> str:
        if not self.settings:
            return "fa5s.folder"

        norm_path = path.replace("\\", "/").rstrip("/").lower()
        for config in self.settings.folder_configs:
            cfg_path = config.get("path", "").replace("\\", "/").rstrip("/").lower()
            if norm_path == cfg_path:
                return config.get("icon", "fa5s.folder")

        return "fa5s.folder"

    def _has_valid_media_folders(self) -> bool:
        """Return True if settings contains at least one existing media folder path."""
        if not self.settings:
            return False
        import os

        for config in self.settings.folder_configs:
            p = config.get("path", "")
            if p and os.path.isdir(p):
                return True
        return False

    def update_folder_list_by_path(self, path: str) -> None:
        # if not path:
        #     self.folder_view.show_empty_state()
        #     self.title_label.setText("Folders")
        #     self.help_icon.setToolTip("")
        #     return

        # No path provided -> show empty state. If no configured media folders,
        # instruct the user to add media in settings.
        if not self._has_valid_media_folders():
            self.folder_view.show_empty_state(message=_EMPTY_STATE_NO_MEDIA_FOLDERS)
            return

        items = self.file_util.get_files_from_path(path)
        folder_items = [item for item in items if item.is_dir]

        count = len(folder_items)
        self.title_label.setText(f"Folders ({count})")

        tooltip = (
            f"Folders in list: {count}\n\n"
            f"Folder List Usage:\n"
            f"- Single-Click, select a folder to view its contents\n"
            f"- Use 'Add Media Folder' in Settings (Gear icon) to add more media folders\n"
            f"- Use the folder picker to browse other directories"
            f"- Use the scrollbar or mouse wheel to browse files"
        )
        self.help_icon.setToolTip(tooltip)

        # if not folder_items:
        #     self.folder_view.show_empty_state(path)
        #     return

        # No folders under the given root. If there are no configured/valid
        # media folders show an instruction to add them; otherwise show path.
        if not self._has_valid_media_folders():
            self.folder_view.show_empty_state(message=_EMPTY_STATE_NO_MEDIA_FOLDERS)
            return

        current_selection = self.folder_view.property("last_selected_folder")
        self.folder_view.clear()
        for item in folder_items:
            icon_name = self._get_icon_for_path(item.full_path)
            self.folder_view.add_folder_item(item, icon_name)

        if current_selection:
            self.folder_view.set_selected_folder(current_selection)

    def update_folder_list_by_items(self, items: list[FileUtilModel]) -> None:
        # if not items:
        #     self.folder_view.show_empty_state()
        #     self.title_label.setText("Folders")
        #     self.help_icon.setToolTip("")
        #     return

        # No items passed (e.g., filters returned nothing). If there are no
        # configured media folders, instruct the user to add them in Settings.
        if not self._has_valid_media_folders():
            self.folder_view.show_empty_state(message=_EMPTY_STATE_NO_MEDIA_FOLDERS)
            return

        print(f"folder list: update_folder_list_by_items: items:{len(items)}")
        folder_items = [item for item in items if item.is_dir]
        print(
            f"folder list: update_folder_list_by_items: folder_items:{len(folder_items)}"
        )

        count = len(folder_items)
        self.title_label.setText(f"Folders ({count})")

        tooltip = (
            f"Folders in list: {count}\n\n"
            f"Folder List Usage:\n"
            f"- Click a folder to view its contents\n"
            f"- Use 'Add Media Folder' in settings to add more roots\n"
            f"- Use the folder picker to browse other directories"
        )
        self.help_icon.setToolTip(tooltip)

        # if not folder_items:
        #     self.folder_view.show_empty_state()
        #     return

        # Filters yielded no matching folder items. Show instruction if
        # there are no configured/valid media folders.
        if not self._has_valid_media_folders():
            self.folder_view.show_empty_state(message=_EMPTY_STATE_NO_MEDIA_FOLDERS)
            return

        current_selection = self.folder_view.property("last_selected_folder")
        self.folder_view.clear()
        for item in folder_items:
            icon_name = self._get_icon_for_path(item.full_path)
            self.folder_view.add_folder_item(item, icon_name)

        if current_selection:
            self.folder_view.set_selected_folder(current_selection)

    def apply_theme(self) -> None:
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)

        self._container.setStyleSheet(APP_THEME.container_qss())
        self._container.setFont(font)

        self.title_label.setStyleSheet(APP_THEME.label_qss())
        self.help_icon.setStyleSheet(
            APP_THEME.label_qss("small")
            + "; border: 1px solid palette(text); border-radius: 8px;"
        )

        self.folder_view.setStyleSheet(APP_THEME.list_qss())
        self.folder_view.setFont(font)
