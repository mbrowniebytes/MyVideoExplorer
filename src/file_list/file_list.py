import os

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.file_list.file_list_view import FileListView
from src.theme.theme import APP_THEME
from src.utils.file_util import FileUtil
from src.widgets.base_widget import BaseWidget


class FileList(BaseWidget):
    sig_file_selected_intent = Signal(str)

    def __init__(self, file_util: FileUtil, log_util) -> None:
        super().__init__(log_util)
        self.title_widget = QWidget()
        self.file_view = FileListView()
        self.file_util = file_util
        self._signals_connected = False
        self._container = QWidget()

    def build(self):
        self._container = self._build_container()
        layout = QVBoxLayout(self._container)

        self.title_widget = self._build_title_widget()
        layout.addWidget(self.title_widget)
        layout.addWidget(self.file_view)

        self.connect_sigs()
        return self._container

    def _build_container(self) -> QWidget:
        container = QWidget()
        container.setObjectName("fileListContainer")
        container.setStyleSheet(APP_THEME.container_qss())
        container.setFixedHeight(120)
        return container

    def _build_title_widget(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.title_label = QLabel("Folder Contents:")
        self.title_label.setStyleSheet(APP_THEME.label_qss("small"))

        self.help_icon = QLabel("?")
        self.help_icon.setStyleSheet(APP_THEME.help_icon_label_qss())
        self.help_icon.setFixedSize(16, 16)
        self.help_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.explorer_button = QToolButton()
        self.explorer_button.setText("Open Folder")
        # self.explorer_button.setToolButtonStyle(
        #     Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        # )
        self.explorer_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.explorer_button.setIcon(
            APP_THEME.icon("fa5s.folder", color=APP_THEME.text_color)
        )
        self.explorer_button.setIconSize(
            QSize(APP_THEME.icon_size, APP_THEME.icon_size)
        )
        self.explorer_button.setStyleSheet(APP_THEME.small_button_qss())
        self.explorer_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.explorer_button.clicked.connect(self._on_open_folder_clicked)
        self.explorer_button.setVisible(False)

        layout.addWidget(self.title_label)
        layout.addWidget(self.help_icon)
        layout.addStretch()
        layout.addWidget(self.explorer_button)

        return widget

    def _on_open_folder_clicked(self) -> None:
        folder_path = self.file_view.property("current_folder")
        if folder_path and os.path.exists(folder_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))

    def _handle_file_selected_intent(self, file_path: str) -> None:
        self.sig_file_selected_intent.emit(file_path)
        self.log_util.debug(f"sig_file_selected_intent emitted for: {file_path}")

    def connect_sigs(self):
        if self._signals_connected:
            return
        self.file_view.sig_file_selected.connect(self._handle_file_selected_intent)
        self.file_view.connect_sigs()
        self._signals_connected = True

    def refresh(self, folder_path: str) -> None:
        if self.file_view.property("current_folder") == folder_path:
            return
        self.update_file_list(folder_path)

    def set_selected_file(self, file_path: str) -> None:
        self.file_view.set_selected_file(file_path)

    def update_file_list(self, folder_path: str) -> None:
        self.file_view.setProperty("current_folder", folder_path)
        self.file_view.clear()

        if not folder_path:
            self.title_label.setText("Folder Contents:")
            self.help_icon.setToolTip("")
            self.explorer_button.setVisible(False)
            return

        items = self.file_util.get_child_files(folder_path)
        for item in items:
            self.file_view.add_file_item(item)

        count = len(items)
        self.title_label.setText(f"Folder Contents: ({count})")
        tooltip = (
            f"Files in folder: {count}\n\n"
            f"File List Usage:\n"
            f"- Double-click video to play it\n"
            f"- Single-click, selected image will be shown above\n"
            f"- Use the scrollbar or mouse wheel to browse files"
        )
        self.help_icon.setToolTip(tooltip)

        self.explorer_button.setVisible(True)

        # Ensure the list widget logic is set up (theming/connections)
        if not self._signals_connected:
            self.connect_sigs()

    def apply_theme(self) -> None:
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self._container.setStyleSheet(APP_THEME.container_qss())
        self._container.setFont(font)

        self.title_label.setStyleSheet(APP_THEME.label_qss("small"))
        self.help_icon.setStyleSheet(
            APP_THEME.label_qss("small")
            + "; border: 1px solid palette(text); border-radius: 8px;"
        )
        self.explorer_button.setStyleSheet(APP_THEME.small_button_qss())

        self.file_view.apply_theme()
