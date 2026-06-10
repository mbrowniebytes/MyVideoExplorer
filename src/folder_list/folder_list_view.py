import os
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from src.theme.theme import APP_THEME
from src.utils.file_util_model import FileUtilModel


class FolderListView(QListWidget):
    sig_folder_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._empty_state_text = "No folders found."
        self._loading_state_text = "Loading..."
        self.itemClicked.connect(self._on_item_clicked)
        APP_THEME.setup_list_widget(self)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        folder_path = item.data(Qt.ItemDataRole.UserRole)
        if folder_path:
            # Emit first to let controller update
            self.sig_folder_selected.emit(folder_path)

    def show_loading_state(self) -> None:
        self.clear()
        loading_item = QListWidgetItem(self._loading_state_text)
        loading_item.setFlags(Qt.ItemFlag.NoItemFlags)
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
        self.sig_folder_selected.emit(folder_path)
