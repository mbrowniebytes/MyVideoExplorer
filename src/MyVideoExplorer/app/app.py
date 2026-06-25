import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.app.app_container import AppContainer
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil


class App:
    def __init__(
        self,
        app: QApplication,
        container: AppContainer,
    ) -> None:
        self.window: QMainWindow = QMainWindow()
        self.app = app
        self.container = container

        self.font_util = container.font_util

        self.controller = container.controller
        self.folder_nav = container.folder_nav
        self.folder_list = container.folder_list
        self.file_list = container.file_list
        self.image_list = container.image_list
        self.media_tabs = container.media_info_tabs
        self.video_player = container.video_player
        self.media_info = container.media_info

    def build(self) -> QMainWindow:
        self.font_util.load_custom_fonts(Path("assets/fonts"))

        self._create_app_icon()
        self.window.setWindowTitle("MyVideoExplorer")
        self.window.resize(1400, 900)

        central_widget = QWidget()
        main_layout = QHBoxLayout()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(APP_THEME.splitter_qss())

        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 900])

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        self.window.setCentralWidget(central_widget)

        APP_THEME.app = self.app
        APP_THEME.refresh_theme(self.window)

        return self.window

    def _create_app_icon(self):
        path_to_icon = FileUtil.get_resource_path("assets/app.png")
        pixmap = QPixmap()
        pixmap.loadFromData(Path(path_to_icon).read_bytes())
        appIcon = QIcon(pixmap)
        self.app.setWindowIcon(appIcon)

    def _create_left_panel(self) -> QWidget:
        folder_nav_widget = self.folder_nav.build()

        file_container = QWidget()
        layout_folder_file = QVBoxLayout(file_container)
        layout_folder_file.setContentsMargins(0, 0, 0, 0)
        layout_folder_file.setSpacing(0)
        layout_folder_file.addWidget(folder_nav_widget, 0)
        layout_folder_file.addWidget(self.folder_list.build(), 1)
        return file_container

    def _create_right_panel(self) -> QWidget:
        self.image_list.image_list_view.media_info_side_view = (
            self.media_info.media_info_side_view
        )

        return self.media_tabs.build()

    def initialize(self) -> None:
        self._initialize_app_state()

    def _initialize_app_state(self) -> None:
        # Initialize app by iterating over all configured Media folders.
        # For each valid folder path, set it as the current root so the
        # UI components (folder nav, folder list, image list) refresh.
        media_configs = self.container.settings.settings_data_model.folder_configs
        valid_paths = []
        for media_folder_config in media_configs:
            path_string = media_folder_config.get("path", "")
            if not path_string:
                continue
            try:
                # real_path = os.path.realpath(path_string)
                real_path = Path(path_string).as_posix()
            except Exception:
                continue
            if os.path.isdir(real_path):
                valid_paths.append(real_path)

        # If we have at least one valid media folder, iterate and set each so
        # the container refreshes components for each root. Otherwise leave
        # the controller with an empty selection which will show the empty state.
        if valid_paths:
            # Let controller handle multiple roots at once
            self.controller.set_root_folders(valid_paths)
        else:
            # No valid media folders configured - emit empty selection so UI
            # shows the instruction to add media folders in settings.
            self.controller.set_root_folders([])

    # def refresh_theme(self) -> None:
    #     if self.window is None:
    #         return
    #     APP_THEME.refresh_theme(self.app, root_widget=self.window)
