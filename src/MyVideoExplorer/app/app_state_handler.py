import os
from pathlib import Path
from PySide6.QtWidgets import QMainWindow
from MyVideoExplorer.app.app_container import AppContainer

class AppStateHandler:
    def __init__(self, container: AppContainer, window: QMainWindow) -> None:
        self.container = container
        self.window = window
        self.controller = container.controller

    def initialize(self) -> None:
        self.window.setUpdatesEnabled(False)
        self._initialize_app_state()
        self.container.resize_window(self.window)
        self.window.setUpdatesEnabled(True)

    def _initialize_app_state(self) -> None:
        media_configs = self.container.settings.settings_data_model.media_configs
        valid_paths = []
        for media_folder_config in media_configs:
            path_string = media_folder_config.get("path", "")
            if not path_string:
                continue
            try:
                real_path = Path(path_string).as_posix()
            except Exception:
                continue
            if os.path.isdir(real_path):
                valid_paths.append(real_path)

        if valid_paths:
            self.controller.set_root_folders(valid_paths)
        else:
            self.controller.set_root_folders([])

    def close(self) -> None:
        prior_folder = self.controller.state.current_folder
        window_size = self.window.size()
        app_size = ""
        if window_size:
            app_height = window_size.height()
            app_width = window_size.width()
            app_size = f"{app_width}x{app_height}"

        window_pos = self.window.pos()
        app_pos = ""
        if window_pos:
            app_pos = f"{window_pos.x()},{window_pos.y()}"

        settings = {
            "prior_folder": prior_folder,
            "app_size": app_size,
            "app_pos": app_pos,
        }
        self.container.settings.settings_data_model.save_state(settings)

        self.container.log_util.log_memory("Application closing...")
        self.container.log_util.close()
