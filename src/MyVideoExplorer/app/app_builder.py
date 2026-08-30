from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.app.app_container import AppContainer

DEFAULT_SPLITTER_SIZES = (600, 900)


class AppBuilder:
    def __init__(self, container: AppContainer, app, window: QMainWindow) -> None:
        self.container = container
        self.app = app
        self.window = window

    def build(self) -> QWidget:
        self.container.font_util.load_custom_fonts()

        main_widget = QWidget(self.window)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 0, 2, 0)

        splitter = self._create_splitter()
        splitter.addWidget(self._create_left_panel())
        splitter.addWidget(self._create_right_panel())
        splitter.setSizes(list(DEFAULT_SPLITTER_SIZES))
        main_layout.addWidget(splitter)

        APP_THEME.app = self.app
        APP_THEME.refresh_theme(self.window)

        return main_widget

    def _create_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(APP_THEME.splitter_qss())
        splitter.setContentsMargins(0, 8, 0, 2)
        return splitter

    def _create_left_panel(self) -> QWidget:
        folder_nav_widget = self.container.folder_nav.build()

        file_container = QWidget(self.window)
        layout_folder_file = QVBoxLayout(file_container)
        layout_folder_file.setContentsMargins(0, 0, 0, 0)
        layout_folder_file.setSpacing(2)
        layout_folder_file.addWidget(folder_nav_widget, 0)
        layout_folder_file.addWidget(self.container.folder_list.build(), 1)
        return file_container

    def _create_right_panel(self) -> QWidget:
        self.container.image_list.image_list_view.media_info_side_view = (
            self.container.media_info.media_info_side_view
        )

        return self.container.media_info_tabs.build()
