from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QVBoxLayout

from src.folder_filter.folder_filter import FolderFilters
from src.theme.theme import APP_THEME
from src.widgets.base_widget import BaseWidget
from PySide6.QtCore import QTimer

class FolderNav(BaseWidget):
    """
    Navigation sidebar combining folder selection buttons and filters.
    """

    sig_root_folder = Signal(str)
    sig_selected_folder = Signal(str)
    sig_selected_items = Signal(list)
    sig_genre_changed = Signal(str)

    def __init__(self, folder_nav_filters: FolderFilters, log_util) -> None:
        super().__init__(log_util)
        self.root_folders: list[str] = []
        self.folder_nav_filters = folder_nav_filters
        self._signals_connected = False

    def build(self) -> FolderNav:
        """Builds the navigation UI and connects internal signals."""
        self.folder_nav_filters.build()

        layout = self.set_compact_layout(QVBoxLayout)
        layout.setSpacing(10)
        layout.addWidget(self.folder_nav_filters)

        self._connect_sigs()
        return self

    def _handle_root_folder(self, path: str) -> None:
        self.sig_root_folder.emit(path)
        self.log_util.debug(f"sig_root_folder emitted with: {path}")

    def _handle_genre_changed(self, genre: str) -> None:
        self.sig_genre_changed.emit(genre)
        self.log_util.debug(f"sig_genre_changed emitted with: {genre}")

    def _connect_sigs(self) -> None:
        if self._signals_connected:
            return
        self.folder_nav_filters.sig_root_folder.connect(self._handle_root_folder)
        self.folder_nav_filters.sig_apply_filters.connect(self.apply_filters)
        self.folder_nav_filters.sig_genre_changed.connect(self._handle_genre_changed)
        self._signals_connected = True

    def set_root_folder(self, paths: list[str]) -> None:
        """Sets the root folder for both buttons and filters."""

        print(f"folder nav: set_root_folder: paths:{paths}")
        self.root_folders = paths
        self.folder_nav_filters.root_folders = paths

        # Defer UI rebuild to the event loop to avoid rebuilding during
        # signal processing; ensure nav combo and media buttons reflect
        # the full list of configured roots.

        def _refresh_filters() -> None:
            try:
                # Rebuild nav combo (labels) and saved filters combo
                self.folder_nav_filters.build_nav_combo()
                # self.folder_nav_filters._refresh_saved_filters_combo()
                # Rebuild media buttons to reflect current settings and roots
                self.folder_nav_filters.media_filter.refresh_buttons()

                self.apply_filters()
            except Exception:
                # Safe-guard: don't crash if methods are not present yet
                pass

        # required .. timing issue?
        QTimer.singleShot(0, _refresh_filters)


    def apply_filters(self) -> None:
        """Applies filters and emits results."""
        # Let FolderNavFilters choose a default root (first configured) when
        # no explicit folder is passed.
        filtered_items = self.folder_nav_filters.apply_filters()
        # print(f"folder nav: apply_filters: filtered_items:{len(filtered_items)}")
        self.sig_selected_items.emit(filtered_items)
        self.log_util.debug(f"sig_selected_items emitted with {len(filtered_items)} items")

    def apply_theme(self) -> None:
        """Applies theme to itself and nested navigation components."""
        super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size - 15)
        self.setFont(font)

        self.folder_nav_filters.apply_theme()
