from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.folder_filter.folder_filter import FolderFilters
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.ui_utils import UIUtils


class FolderNav(QWidget, ThemableMixin):
    """
    Navigation sidebar combining folder selection buttons and filters.
    """

    root_folder_changed = Signal(object)
    selected_folder_changed = Signal(object)
    filtered_items_updated = Signal(object)
    genre_changed = Signal(object)

    def __init__(self, folder_filter_widget: FolderFilters, log_util: LogUtil) -> None:
        super().__init__()
        self.log_util = log_util
        self._ui_utils = UIUtils()
        self.root_folders: list[str] = []
        self.folder_filter_widget = folder_filter_widget
        self._signals_connected = False

        # self._timer = QTimer(self)
        # self._timer.setSingleShot(True)

    def build(self) -> FolderNav:
        """Builds the navigation UI and connects internal signals."""
        self.folder_filter_widget.build()

        layout = self._ui_utils.apply_compact_layout(self, QVBoxLayout)
        layout.setSpacing(10)
        layout.addWidget(self.folder_filter_widget)

        self._connect_sigs()
        return self

    def _handle_root_folder(self, payload: SignalPayload) -> None:
        self.root_folder_changed.emit(payload)
        self.log_util.debug(f"root_folder_changed emitted with: {payload.data}")

    def _handle_genre_changed(self, payload: SignalPayload) -> None:
        self.genre_changed.emit(payload)
        self.log_util.debug(f"genre_changed emitted with: {payload.data}")

    def _connect_sigs(self) -> None:
        if self._signals_connected:
            return
        self.folder_filter_widget.root_folder.connect(self._handle_root_folder)
        self.folder_filter_widget.filters_requested.connect(self.apply_filters)
        self.folder_filter_widget.genre_changed.connect(self._handle_genre_changed)
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

            # self.apply_filters_requested()
            QTimer.singleShot(150, lambda: self.apply_filters())
        except Exception as e:
            self.log_util.error(f"Error in _refresh_filters: {e}")
            # Safe-guard: don't crash if methods are not present yet
            pass

    def apply_filters(self) -> None:
        """Applies filters and emits results."""
        # Let FolderNavFilters choose a default root (first configured) when
        # no explicit folder is passed.
        # QTimer.singleShot(wait, lambda: self.folder_filter_widget.apply_filters_requested(on_complete=self._on_filters_applied))
        self.folder_filter_widget.apply_filters(on_complete=self._on_filters_applied)
        # self._timer.timeout.connect(lambda: self.folder_filter_widget.apply_filters_requested(on_complete=self._on_filters_applied))
        # self._timer.start(150)

    def _on_filters_applied(self, filtered_items: list[FileUtilModel]) -> None:
        payload = SignalPayload(
            data=filtered_items,
            sender=self.__class__.__name__,
            name="Filtered Items Updated",
            description="Emitted when filtered items are updated.",
            flow=SignalFlow.USER_INPUT,
        )
        self.filtered_items_updated.emit(payload)
        if self.log_util:
            self.log_util.debug(
                f"filtered_items_updated emitted with {len(filtered_items)} items"
            )

        # if filtered_items and filtered_items[0] and filtered_items[0].full_path:
        #     print(f"folder nav: _on_filters_applied: first folder:{filtered_items[0]}")
        #     payload = SignalPayload(
        #         data=filtered_items[0].full_path,
        #         sender=self.__class__.__name__,
        #         name="Auto Select First Folder",
        #         description="Emitted when filtered items are updated.",
        #         flow=SignalFlow.COMPONENT_INTERACTION,
        #     )

    def apply_theme(self) -> None:
        """Applies theme to itself and nested navigation components."""
        # super().apply_theme()
        self.folder_filter_widget.apply_theme()
