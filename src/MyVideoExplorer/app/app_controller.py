from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QObject

from MyVideoExplorer.app.app_signals import SignalRegistry
from MyVideoExplorer.app.app_state import AppState
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.log_util import LogUtil


class AppController(QObject):
    """
    Single source of truth for app state.
    Emits specific signals so subscribers only react to what changed.
    """

    def __init__(self, log_util: LogUtil, signals: SignalRegistry) -> None:
        super().__init__()
        self.log_util = log_util
        self.signals = signals
        self.state = AppState()
        self.log_util.debug(f"__init__ {self.__class__.__name__}")

    @staticmethod
    def _normalize_folder_paths(
        folder_paths: Iterable[str] | str | None,
    ) -> list[str]:
        """Normalize path input to a list of unique, non-empty folder paths."""
        if folder_paths is None:
            return []
        iterable: Iterable[str] = [folder_paths] if isinstance(folder_paths, str) else folder_paths

        normalized: list[str] = []
        seen: set[str] = set()
        for folder_path in iterable:
            if not isinstance(folder_path, str):
                continue
            candidate = str(folder_path).strip()
            if not candidate:
                continue
            canonical = FileUtil.normalize_path(candidate)
            if canonical in seen:
                continue
            seen.add(canonical)
            normalized.append(canonical)
        return normalized

    def _emit_signal(self, signal_name: str, value: object) -> None:
        self.signals.emit_payload(signal_name, value, self.__class__.__name__)

    def set_root_folders(self, folder_paths: list[str] | tuple[str, ...] | set[str] | str | None) -> None:
        """Accept a single folder path or an iterable of folder paths."""
        valid_paths = self._normalize_folder_paths(folder_paths)
        self.log_util.debug(
            "Updating root folders",
            extra_info={"root_folders": valid_paths},
        )

        # Update state
        self.state.root_folders = valid_paths
        self.state.root_folder = valid_paths[0] if valid_paths else ""

        # Reset selection state when roots change
        self.state.prior_folder = self.state.current_folder
        self.state.current_folder = self.state.root_folder
        self.state.current_file = ""
        self.state.current_image = ""

        self._emit_signal("root_folders_changed", valid_paths)
        if self.state.root_folder:
            self._emit_signal("root_folder_changed", self.state.root_folder)
        self.log_util.debug(f"root_folders_changed emitted for: {valid_paths}")

    def set_current_folder(self, folder_path: str, force: bool = False) -> None:
        try:
            if not force and self.state.current_folder == folder_path:
                return
            self.state.prior_folder = self.state.current_folder
            self.state.current_folder = folder_path
            self.state.current_file = ""
            self.state.current_image = ""
            self._emit_signal("selected_folder_changed", folder_path)
            self.log_util.debug(f"selected_folder_changed emitted for: {folder_path}")
        except Exception as e:
            self.log_util.error(f"Error setting current folder: {e!s}")

    def set_current_file(self, file_path: str) -> None:
        self.log_util.debug(f"Attempting to set file: {file_path}")
        try:
            if self.state.current_file == file_path:
                return
            self.state.current_file = file_path
            self._emit_signal("file_changed", file_path)
            self.log_util.debug(f"file_changed emitted for: {file_path}")
        except Exception as e:
            self.log_util.error(f"Error setting current file: {e!s}")

    def set_current_image(self, image_path: str) -> None:
        if self.state.current_image == image_path:
            return
        self.state.current_image = image_path
        self._emit_signal("image_changed", image_path)
        self.log_util.debug(f"image_changed emitted for: {image_path}")

    def set_current_tab(self, tab_index: int) -> None:
        if self.state.current_tab == tab_index:
            return
        self.state.current_tab = tab_index
        self._emit_signal("tab_changed", tab_index)

    def emit_current_selection(self) -> None:
        if self.state.current_folder:
            self._emit_signal("selected_folder_changed", self.state.current_folder)
            self.log_util.debug(
                f"selected_folder_changed emitted for: {self.state.current_folder}"
            )
        if self.state.current_file:
            self._emit_signal("file_changed", self.state.current_file)
            self.log_util.debug(
                f"file_changed emitted for: {self.state.current_file}"
            )
