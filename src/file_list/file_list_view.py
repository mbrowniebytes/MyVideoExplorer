from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon, QFont, QResizeEvent
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from src.app.app_signals_model import SignalPayload, SignalFlow
from src.theme.theme import APP_THEME
from src.utils.file_util_model import FileUtilModel


class FileListView(QListWidget):
    sig_file_selected = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._signals_connected = False
        self.set_style()

    def set_style(self):
        # self.setStyleSheet(APP_THEME.list_qss())
        # self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        # APP_THEME.setup_list_widget(self)
        self.apply_theme()

        self.setViewMode(QListWidget.ViewMode.ListMode)
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setWrapping(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSpacing(10)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_icon_size()

    def _update_icon_size(self):
        # Adjust icon size to fit the height of the list view
        # We need to account for padding/margins
        height = self.viewport().height()
        # In ListMode, the item contains icon on the left and text on the right.
        # Since we want the icon to "fit and resize to FileListView height",
        # we can make it nearly as tall as the viewport.

        # Leave some space for padding (top/bottom)
        size = max(16, height - 20)
        self.setIconSize(QSize(size, size))

    def connect_sigs(self):
        if self._signals_connected:
            return
        self.itemClicked.connect(self._emit_file_selected)
        self._signals_connected = True

    def _emit_file_selected(self, item: QListWidgetItem) -> None:
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            payload = SignalPayload(
                data=file_path,
                sender=self.__class__.__name__,
                name="File Selected",
                description="Emitted when a file is selected in FileListView.",
                flow=SignalFlow.USER_INPUT,
            )
            self.sig_file_selected.emit(payload)

    def add_file_item(self, item: FileUtilModel) -> None:
        icon = self._get_icon(item.file_type)
        list_item = QListWidgetItem(icon, item.name)
        list_item.setData(Qt.ItemDataRole.UserRole, item.full_path)

        tooltip = f"Name: {item.name}\nType: {item.file_type or 'Unknown'}\nPath: {item.full_path}"
        list_item.setToolTip(tooltip)

        self.addItem(list_item)

    def _get_icon(self, file_type: str | None) -> QIcon:
        icon_name = "fa5s.file"

        if file_type == "video":
            icon_name = "fa5s.file-video"
        elif file_type in ("image", "poster"):
            icon_name = "fa5s.file-image"
        elif file_type == "nfo":
            icon_name = "fa5s.file-alt"
        else:
            icon_name = "fa5s.file"

        return APP_THEME.icon(icon_name, color=APP_THEME.text_color)

    def set_selected_file(self, file_path: str) -> None:
        if not file_path:
            self.setCurrentRow(-1)
            return

        for row in range(self.count()):
            item = self.item(row)
            if item and item.data(Qt.ItemDataRole.UserRole) == file_path:
                self.setCurrentRow(row)
                self.scrollToItem(item)
                return

        self.setCurrentRow(-1)

    def apply_theme(self) -> None:
        self.setStyleSheet(APP_THEME.list_qss())
        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self._update_icon_size()
