from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QVBoxLayout

from src.app.app_signals_model import SignalPayload, SignalFlow
from src.folder_filter.folder_filter import FolderFilters
from src.theme.theme import APP_THEME
from src.utils.file_util_model import FileUtilModel
from src.widgets.base_widget import BaseWidget
from PySide6.QtCore import QTimer

class FolderNav(BaseWidget):
    """
    Navigation sidebar combining folder selection buttons and filters.
    """

    sig_root_folder = Signal(object)
    sig_selected_folder = Signal(object)
    sig_selected_items = Signal(object)
    sig_genre_changed = Signal(object)

    def __init__(self, folder_filter_widget: FolderFilters, log_util) -> None:
        super().__init__(log_util)
        self.root_folders: list[str] = []
        self.folder_filter_widget = folder_filter_widget
        self._signals_connected = False

    def build(self) -> FolderNav:
        """Builds the navigation UI and connects internal signals."""
        self.folder_filter_widget.build()

        layout = self.set_compact_layout(QVBoxLayout)
        layout.setSpacing(10)
        layout.addWidget(self.folder_filter_widget)

        self._connect_sigs()
        return self

    def _handle_root_folder(self, payload: SignalPayload) -> None:
        self.sig_root_folder.emit(payload)
        self.log_util.debug(f"sig_root_folder emitted with: {payload.data}")

    def _handle_genre_changed(self, payload: SignalPayload) -> None:
        self.sig_genre_changed.emit(payload)
        self.log_util.debug(f"sig_genre_changed emitted with: {payload.data}")

    def _connect_sigs(self) -> None:
        if self._signals_connected:
            return
        self.folder_filter_widget.sig_root_folder.connect(self._handle_root_folder)
        self.folder_filter_widget.sig_apply_filters.connect(self.apply_filters)
        self.folder_filter_widget.sig_genre_changed.connect(self._handle_genre_changed)
        self._signals_connected = True

    def set_root_folders(self, paths: list[str]) -> None:
        """Sets the root folder for both buttons and filters."""

        print(f"folder nav: set_root_folders: paths:{paths}")
        self.root_folders = paths
        self.folder_filter_widget.root_folders = paths

        self._refresh_filters()

    def _refresh_filters(self) -> None:
        try:
            # Rebuild nav combo (labels) and saved filters combo
            self.folder_filter_widget.build_nav_combo()
            # self.folder_filter_widget._refresh_saved_filters_combo()
            # Rebuild media buttons to reflect current settings and roots
            self.folder_filter_widget.media_filter_widget.refresh_buttons()

            QTimer.singleShot(150, lambda: self.apply_filters())
        except Exception as e:
            self.log_util.error(f"Error in _refresh_filters: {e}")
            # Safe-guard: don't crash if methods are not present yet
            pass


    def apply_filters(self) -> None:
        """Applies filters and emits results."""
        # Let FolderNavFilters choose a default root (first configured) when
        # no explicit folder is passed.
        self.folder_filter_widget.apply_filters(on_complete=self._on_filters_applied)

    def _on_filters_applied(self, filtered_items: list[FileUtilModel]) -> None:
        payload = SignalPayload(
            data=filtered_items,
            sender=self.__class__.__name__,
            name="Filtered Items Updated",
            description="Emitted when filtered items are updated.",
            flow=SignalFlow.USER_INPUT,
        )
        self.sig_selected_items.emit(payload)
        self.log_util.debug(f"sig_selected_items emitted with {len(filtered_items)} items")

        if filtered_items and filtered_items[0] and filtered_items[0].full_path:
            print(f"folder nav: set_root_folder: paths:{filtered_items[0]}")
            payload = SignalPayload(
                data=filtered_items[0].full_path,
                sender=self.__class__.__name__,
                name="Auto Select First Folder",
                description="Emitted when filtered items are updated.",
                flow=SignalFlow.COMPONENT_INTERACTION,
            )
            self.sig_selected_folder.emit(payload)

    def apply_theme(self) -> None:
        """Applies theme to itself and nested navigation components."""
        super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size - 15)
        self.setFont(font)

        self.folder_filter_widget.apply_theme()
