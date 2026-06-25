from __future__ import annotations

from PySide6.QtCore import QObject

from MyVideoExplorer.app.app_signals import SignalRegistry
from MyVideoExplorer.app.app_state import AppState
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

    def set_root_folders(self, folder_paths: list[str] | str) -> None:
        """Accept a single folder path or an iterable of folder paths.

        When given an iterable, the controller will iterate and emit the
        existing `sig_root_folder`/`sig_selected_folder` for each valid path.
        The `state.root_folders` list is updated and `state.root_folder` is set
        to the first valid path (or empty string if none).
        """
        paths = folder_paths
        print(f"app:set_root_folders: paths:{paths}")

        valid_paths: list[str] = []
        for p in paths:
            if not p:
                continue
            # Avoid emitting duplicate consecutive roots
            if valid_paths and valid_paths[-1] == p:
                continue
            valid_paths.append(p)

        # Update state
        self.state.root_folders = valid_paths
        self.state.root_folder = valid_paths[0] if valid_paths else ""

        # Reset selection state when roots change
        self.state.current_folder = self.state.root_folder
        self.state.current_file = ""
        self.state.current_image = ""

        # Emit a single signal with all roots so FolderNav can show them all at once
        # if valid_paths:
        payload = self.signals.create_payload(
            "sig_root_folders", valid_paths, self.__class__.__name__
        )
        self.signals.sig_root_folders.emit(payload)
        self.log_util.debug(f"sig_root_folders emitted for: {valid_paths}")

        # Also keep emitting per-root signals for backward compatibility so
        # existing listeners (FolderList, ImageList, MediaInfo) still refresh.
        # for vp in valid_paths:
        #     self.sig_root_folder.emit(vp)
        # self.sig_selected_folder.emit(vp)

    def set_current_folder(self, folder_path: str, force: bool = False) -> None:
        # self.log_util.debug(f"Attempting to set folder: {folder_path}")
        try:
            if not force and self.state.current_folder == folder_path:
                return
            self.state.current_folder = folder_path
            self.state.current_file = ""
            self.state.current_image = ""
            payload = self.signals.create_payload(
                "sig_selected_folder", folder_path, self.__class__.__name__
            )
            self.signals.sig_selected_folder.emit(payload)
            self.log_util.debug(f"sig_selected_folder emitted for: {folder_path}")
        except Exception as e:
            self.log_util.error(f"Error setting current folder: {str(e)}")

    def set_current_file(self, file_path: str) -> None:
        self.log_util.debug(f"Attempting to set file: {file_path}")
        try:
            if self.state.current_file == file_path:
                return
            self.state.current_file = file_path
            payload = self.signals.create_payload(
                "sig_file_changed", file_path, self.__class__.__name__
            )
            self.signals.sig_file_changed.emit(payload)
            self.log_util.debug(f"sig_file_changed emitted for: {file_path}")
        except Exception as e:
            self.log_util.error(f"Error setting current file: {str(e)}")

    def set_current_image(self, image_path: str) -> None:
        if self.state.current_image == image_path:
            return
        self.state.current_image = image_path
        payload = self.signals.create_payload(
            "sig_image_changed", image_path, self.__class__.__name__
        )
        self.signals.sig_image_changed.emit(payload)
        self.log_util.debug(f"sig_image_changed emitted for: {image_path}")

    def set_current_tab(self, tab_index: int) -> None:
        if self.state.current_tab == tab_index:
            return
        self.state.current_tab = tab_index
        payload = self.signals.create_payload(
            "sig_tab_changed", tab_index, self.__class__.__name__
        )
        self.signals.sig_tab_changed.emit(payload)
        # self.log_util.debug(f"sig_tab_changed emitted for: {tab_index}")

    def emit_current_selection(self) -> None:
        if self.state.current_folder:
            payload = self.signals.create_payload(
                "sig_selected_folder",
                self.state.current_folder,
                self.__class__.__name__,
            )
            self.signals.sig_selected_folder.emit(payload)
            self.log_util.debug(
                f"sig_selected_folder emitted for: {self.state.current_folder}"
            )
        if self.state.current_file:
            payload = self.signals.create_payload(
                "sig_file_changed", self.state.current_file, self.__class__.__name__
            )
            self.signals.sig_file_changed.emit(payload)
            self.log_util.debug(
                f"sig_file_changed emitted for: {self.state.current_file}"
            )
