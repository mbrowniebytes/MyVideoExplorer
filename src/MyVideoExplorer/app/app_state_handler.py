from pathlib import Path

from PySide6.QtWidgets import QMainWindow

from MyVideoExplorer.app.app_container import AppContainer
from MyVideoExplorer.utils.file_util import FileUtil


class AppStateHandler:
    def __init__(self, container: AppContainer, window: QMainWindow) -> None:
        self.container = container
        self.window = window
        self.controller = container.controller

    @staticmethod
    def _normalize_root_path(path_string: str) -> str:
        """Return a canonical directory path suitable for comparison and storage."""
        return FileUtil.normalize_path(path_string)

    @classmethod
    def _collect_valid_root_paths(cls, media_configs: list[dict]) -> list[str]:
        valid_paths: list[str] = []
        seen: set[str] = set()

        for media_folder_config in media_configs:
            if not isinstance(media_folder_config, dict):
                continue
            path_string = str(media_folder_config.get("path", "")).strip()
            if not path_string:
                continue
            try:
                real_path = cls._normalize_root_path(path_string)
            except Exception:
                continue
            path_obj = Path(real_path)
            if path_obj.is_dir() and real_path not in seen:
                seen.add(real_path)
                valid_paths.append(real_path)

        return valid_paths

    def initialize(self) -> None:
        self.window.setUpdatesEnabled(False)
        self._initialize_app_state()
        self.container.resize_window(self.window)
        self.window.setUpdatesEnabled(True)

    def _initialize_app_state(self) -> None:
        media_configs = self.container.settings.settings_data_model.media_configs
        valid_paths = self._collect_valid_root_paths(media_configs)
        self.controller.set_root_folders(valid_paths)

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
