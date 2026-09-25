from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.folder_list.folder_list_header import FolderListHeader
from MyVideoExplorer.folder_list.folder_list_view import FolderListView
from MyVideoExplorer.folder_list.folder_navigation_controller import (
    FolderNavigationController,
)
from MyVideoExplorer.settings.settings import Settings
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.ui_utils import UIUtils

_EMPTY_STATE_NO_MEDIA_FOLDERS = (
    "No media folders configured.\nOpen Settings (Gear) → Media and add a media folder."
)


class FolderList(QWidget, ThemableMixin):
    folder_selected_intent = Signal(object)
    folder_navigation_requested = Signal(object)
    HISTORY_FOLDER_LENGTH = 100

    def __init__(
        self, file_util: FileUtil, settings: Settings, log_util: LogUtil, parent=None
    ) -> None:
        super().__init__(parent)
        self.log_util = log_util
        self._ui_utils = UIUtils()
        self.folder_list_view = FolderListView(log_util=self.log_util)
        self.loading_label = QLabel("Loading...", parent=self)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stack = QStackedWidget(self)
        self.stack.addWidget(self.folder_list_view)
        self.stack.addWidget(self.loading_label)
        self.file_util = file_util
        self.settings = settings
        self._signals_connected = False
        self._container = QWidget(self)
        self.header = FolderListHeader(parent=self)
        self.navigation_controller = FolderNavigationController()

    @property
    def title_label(self):
        return self.header.title_label

    @property
    def help_icon(self):
        return self.header.help_icon

    @property
    def backward_folder_button(self):
        return self.header.backward_folder_button

    @property
    def forward_folder_button(self):
        return self.header.forward_folder_button

    @property
    def random_folder_button(self):
        return self.header.random_folder_button

    def build(self) -> QWidget:
        self._container = self._build_container()
        layout = QVBoxLayout(self._container)

        self.header.backward_clicked.connect(self._on_backward_folder_clicked)
        self.header.forward_clicked.connect(self._on_forward_folder_clicked)
        self.header.random_clicked.connect(self._on_random_folder_clicked)

        layout.addWidget(self.header)
        layout.addWidget(self.stack)
        self.folder_list_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        if not self._has_valid_media_folders():
            self.folder_list_view.show_empty_state(
                message=_EMPTY_STATE_NO_MEDIA_FOLDERS
            )
            self.stack.setCurrentWidget(self.folder_list_view)
        else:
            self.folder_list_view.show_loading_state()
            self.stack.setCurrentWidget(self.loading_label)

        self.folder_list_view.apply_theme()
        self.connect_sigs()
        return self._container

    def _update_help_tooltip(self) -> None:
        if not self.settings:
            return

        num_folders = len(self.settings.settings_data_model.media_configs)
        if self.settings.settings_data_model.db_enabled():
            loading_source = f"{num_folders} Database{'s' if num_folders != 1 else ''}"
        else:
            loading_source = "File System"

        tooltip = (
            "Folder List Usage:\n"
            "- Click a folder to view its contents\n"
            "- Use 'Add Media Folder' in settings to add more roots\n"
            "- Use the folder picker to browse other directories\n\n"
            f"Settings:\n"
            f"- Checking {num_folders} media folder{'s' if num_folders != 1 else ''}\n"
            f"- Loading from: {loading_source}"
        )
        self.help_icon.setToolTip(tooltip)

    def _build_container(self) -> QWidget:
        container = QWidget(self)
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
            self._update_button_states()
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

        # folder_Filter.apply_filters_requested also loading
        # QTimer.singleShot(250, lambda: self.update_folder_list_by_path(folder_path))

    def _handle_folder_selected_intent(self, payload: SignalPayload) -> None:
        self.folder_selected_intent.emit(payload)
        self.log_util.debug(f"folder_selected_intent emitted for: {payload.data}")

    def connect_sigs(self):
        if self._signals_connected:
            return
        self.folder_list_view.folder_selected.connect(
            self._handle_folder_selected_intent
        )
        if self.settings:
            self.settings.settings_data_model.settings_changed.connect(
                lambda _: self._update_help_tooltip()
            )
        self._signals_connected = True

    def set_selected_folder(self, folder_path: str) -> None:
        self.folder_list_view.set_selected_folder(folder_path)
        self._add_to_history(folder_path)
        # Important: Don't call refresh here as it might trigger a full rebuild

    def show_loading_state(self, folders: list[str] | None = None) -> None:
        self.stack.setCurrentWidget(self.loading_label)
        self.folder_list_view.show_loading_state(folders)
        self._update_button_states()

    def select_next_folder(self, step: int = 1) -> None:
        self.folder_list_view.select_next_folder(step)

    def refresh_icons(self) -> None:
        self.folder_list_view.refresh_icons(self._get_icon_for_path)

    def _has_valid_media_folders(self) -> bool:
        """Return True if settings contains at least one existing media folder path."""
        if not self.settings:
            return False

        for config in self.settings.settings_data_model.media_configs:
            p = config.get("path", "")
            if p and Path(p).is_dir():
                return True
        return False

    # used by tests
    def update_folder_list_by_path(
        self, path: str, on_complete: Callable[[], None] | None = None
    ) -> None:
        """Loads folders from a path and updates the view."""
        self.folder_list_view.show_loading_state([path])
        self.file_util.get_files_from_path_async(
            path,
            on_complete=lambda items: self.populate_view(
                items, on_complete=lambda _: on_complete() if on_complete else None
            ),
        )

    # used by tests
    def update_folder_list_by_items(self, items: list[FileUtilModel]) -> None:
        """Updates the view with a list of items."""
        self.populate_view(items)

    def apply_theme(self) -> None:
        # super().apply_theme()
        self.folder_list_view.apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)

        self._container.setStyleSheet(APP_THEME.container_qss())
        self._container.setFont(font)
        self.folder_list_view.setFont(font)

        self.title_label.setStyleSheet(APP_THEME.label_qss())
        self.help_icon.setStyleSheet(
            APP_THEME.label_qss("small")
            + "; border: 1px solid palette(text); border-radius: 8px;"
        )

        # breaks app theme apply
        # self.folder_list_view.setStyleSheet(APP_THEME.get_list_qss())

    def populate_view(
        self,
        items: list[FileUtilModel],
        on_complete: Callable[[list[FileUtilModel]], None] | None = None,
    ):
        """Sorts and populates the FolderListView."""

        if not items and not self._has_valid_media_folders():
            self.folder_list_view.show_empty_state(
                message=_EMPTY_STATE_NO_MEDIA_FOLDERS
            )
            self.stack.setCurrentWidget(self.folder_list_view)
            self._update_button_states()
            if on_complete:
                on_complete(items)
            return

        def _on_populate_complete(items_result):
            self._update_button_states()
            self.stack.setCurrentWidget(self.folder_list_view)
            if on_complete:
                on_complete(items_result)

        self.folder_list_view.populate_view(
            items,
            get_icon_func=self._get_icon_for_path,
            on_complete=_on_populate_complete,
        )

    def _get_icon_for_path(self, path: str) -> str:
        if not self.settings:
            return "fa6s.folder"

        norm_path = path.lower()
        for config in self.settings.settings_data_model.media_configs:
            cfg_path = config.get("path", "")
            if not cfg_path:
                continue
            cfg_path = Path(cfg_path).as_posix().lower()
            # print(f"_get_icon_for_path: cfg_path: {cfg_path}, norm_path: {norm_path}")
            if norm_path.startswith(cfg_path):
                return config.get("icon", "fa6s.folder")

        return "fa6s.folder"

    def _emit_folder_navigation_requested(self, folder_path: str) -> None:
        payload = SignalPayload(
            data=folder_path,
            sender=self.__class__.__name__,
            name="Folder Navigation Requested",
            description="Emitted when the user requests navigation to a different folder.",
            flow=SignalFlow.USER_INPUT,
        )
        self.folder_navigation_requested.emit(payload)

    def _on_backward_folder_clicked(self) -> None:
        """Handle button click to navigate to prior folder."""
        try:
            folder_path = self.navigation_controller.get_backward_folder()
            if folder_path:
                self._emit_folder_navigation_requested(folder_path)
                self._update_button_states()

        except (IndexError, ValueError) as e:
            self.log_util.error(f"Error navigating to backward folder: {e}")

    def _on_forward_folder_clicked(self) -> None:
        """Handle button click to navigate to forward folder."""
        try:
            folder_path = self.navigation_controller.get_forward_folder()
            if folder_path:
                self._emit_folder_navigation_requested(folder_path)
                self._update_button_states()

        except (IndexError, ValueError) as e:
            self.log_util.error(f"Error navigating to forward folder: {e}")

    def _on_random_folder_clicked(self) -> None:
        """Handle button click to navigate to a random folder."""
        try:
            valid_folders = []
            for row in range(self.folder_list_view.count()):
                item = self.folder_list_view.item(row)
                path = item.data(Qt.ItemDataRole.UserRole)
                if path:
                    valid_folders.append(path)

            folder_path = self.navigation_controller.select_random_folder(valid_folders)
            if folder_path:
                self._emit_folder_navigation_requested(folder_path)
        except (IndexError, ValueError) as e:
            self.log_util.error(f"Error navigating to random folder: {e}")

    def _update_button_states(self) -> None:
        self.header.backward_folder_button.setEnabled(
            self.navigation_controller.can_go_backward()
        )
        self.header.forward_folder_button.setEnabled(
            self.navigation_controller.can_go_forward()
        )

        has_folders = self.folder_list_view.has_folders()
        if self.header.random_folder_button.isEnabled() != has_folders:
            self.header.random_folder_button.setEnabled(has_folders)

    def _add_to_history(self, folder_path: str) -> None:
        self.navigation_controller.add_to_history(folder_path)
        self._update_button_states()
