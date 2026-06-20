import os
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from src.app.app_signals_model import SignalPayload, SignalFlow

from src.theme.theme import APP_THEME
from src.utils.file_util_model import FileUtilModel
from src.utils.log_util import LogUtil


class FolderListView(QListWidget):
    sig_folder_selected = Signal(object)

    def __init__(self, log_util: LogUtil) -> None:
        super().__init__()
        self._empty_state_text = "No folders found."
        self._loading_state_text = "Loading..."
        self._signals_connected = False
        self.connect_sigs()

    def connect_sigs(self):
        if self._signals_connected:
            return
        self.itemClicked.connect(self._on_item_clicked)
        APP_THEME.setup_list_widget(self)
        self._signals_connected = True

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        folder_path = item.data(Qt.ItemDataRole.UserRole)
        if folder_path:
            # Emit first to let controller update
            payload = SignalPayload(
                data=folder_path,
                sender=self.__class__.__name__,
                name="Folder Selected",
                description="Emitted when a folder is selected in FolderListView.",
                flow=SignalFlow.USER_INPUT,
            )
            self.sig_folder_selected.emit(payload)

    def show_loading_state(self, folders: list[str] = None) -> None:
        self.clear()
        text = self._loading_state_text
        if folders:
            text += f"\n\n{',\n'.join(folders)}"
        loading_item = QListWidgetItem(f"\n\n\n {text}")
        loading_item.setFlags(Qt.ItemFlag.NoItemFlags)
        loading_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.addItem(loading_item)

    def show_empty_state(self, root_path: str = "", message: str = "") -> None:
        """Show a friendly empty state in the folder list.

        Args:
            root_path: optional path that produced no results (displayed when provided)
            message: optional custom message to display instead of the default text
        """
        self.clear()
        if message:
            text = message
        elif root_path:
            root_label = os.path.normpath(root_path)
            text = f"No folders found under\n{root_label}"
        else:
            text = "No folders found."

        empty_item = QListWidgetItem(text)
        empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.addItem(empty_item)

    def add_folder_item(
        self, item: FileUtilModel, icon_name: str = "fa5s.folder"
    ) -> None:
        prefix = "  " * item.depth
        if item.depth > 0:
            # prefix += "└─ "
            # prefix += "⤷ "
            # prefix += "." * item.depth
            # prefix += "―" * item.depth
            # prefix += "→"
            prefix += "・" * item.depth
        prefix += " "


        icon = APP_THEME.icon(icon_name, color=APP_THEME.text_color)
        list_item = QListWidgetItem(icon, f"{prefix}{item.name}")
        list_item.setData(Qt.ItemDataRole.UserRole, item.full_path)
        list_item.setData(Qt.ItemDataRole.UserRole + 1, icon_name)
        self.addItem(list_item)

    def refresh_icons(self, get_icon_func) -> None:
        for row in range(self.count()):
            item = self.item(row)
            path = item.data(Qt.ItemDataRole.UserRole)
            if not path:
                continue

            new_icon_name = get_icon_func(path)
            old_icon_name = item.data(Qt.ItemDataRole.UserRole + 1)

            if new_icon_name != old_icon_name:
                icon = APP_THEME.icon(new_icon_name, color=APP_THEME.text_color)
                item.setIcon(icon)
                item.setData(Qt.ItemDataRole.UserRole + 1, new_icon_name)

    def set_selected_folder(self, folder_path: str) -> None:
        if not folder_path:
            if self.currentRow() != -1:
                self.setCurrentRow(-1)
            return

        for row in range(self.count()):
            item = self.item(row)
            if item and item.data(Qt.ItemDataRole.UserRole) == folder_path:
                if self.currentRow() != row:
                    self.setCurrentRow(row)
                    self.scrollToItem(item)
                return

        if self.currentRow() != -1:
            self.setCurrentRow(-1)

    def populate_view(
        self, items: list[FileUtilModel], get_icon_func=None, on_complete: callable = None
    ) -> None:
        """Sorts and populates the FolderListView."""
        folder_items = [item for item in items if item.is_dir]

        if folder_items:
            # Build parent map
            last_at_depth = {}
            # children_map: id(parent) -> list of children
            children_map = {id(None): []}

            for item in folder_items:
                parent = last_at_depth.get(item.depth - 1) if item.depth > 0 else None
                parent_id = id(parent)
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(item)
                last_at_depth[item.depth] = item

            # Sort children
            for parent_id in children_map:
                children_map[parent_id].sort(key=lambda x: x.name.lower())

            # Reconstruct
            sorted_items = []

            def add_sorted_children(parent):
                parent_id = id(parent)
                if parent_id in children_map:
                    for child in children_map[parent_id]:
                        sorted_items.append(child)
                        add_sorted_children(child)

            add_sorted_children(None)
            folder_items = sorted_items

        self.clear()
        for item in folder_items:
            icon_name = get_icon_func(item.full_path) if get_icon_func else "fa5s.folder"
            self.add_folder_item(item, icon_name)

        if on_complete:
            on_complete(items)

    def select_next_folder(self, step: int = 1) -> None:
        if self.count() == 0:
            return

        current_row = self.currentRow()
        if current_row < 0:
            current_row = 0

        new_row = max(0, min(self.count() - 1, current_row + step))
        item = self.item(new_row)
        if item is None:
            return

        folder_path = item.data(Qt.ItemDataRole.UserRole)
        if not folder_path:
            return

        if self.currentRow() == new_row:
            return

        self.setCurrentRow(new_row)
        self.scrollToItem(item)
        payload = SignalPayload(
            data=folder_path,
            sender=self.__class__.__name__,
            name="Folder Selected",
            description="Emitted when a folder is selected in FolderListView.",
            flow=SignalFlow.USER_INPUT,
        )
        self.sig_folder_selected.emit(payload)
