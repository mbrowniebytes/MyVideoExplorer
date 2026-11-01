from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.db.db_filter import DbFilter
from MyVideoExplorer.db.db_filters import DbFilters
from MyVideoExplorer.folder_filter.folder_filter_filter import FolderFilterFilter
from MyVideoExplorer.folder_filter.folder_filter_genre_combo_widget import (
    GenreComboWidget,
)
from MyVideoExplorer.folder_filter.folder_filter_media import FolderFilterMedia
from MyVideoExplorer.folder_filter.folder_filter_table import FolderFilterTable
from MyVideoExplorer.media_nav_search.filter_criteria_dialog import FilterCriteriaDialog
from MyVideoExplorer.settings.settings import Settings
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.utils.file_util import FileUtil, FileUtils
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.ui_utils import UIUtils
from MyVideoExplorer.widgets.buttons.action_button import ActionButton
from MyVideoExplorer.widgets.combo_boxes.select_combo_box import SelectComboBox

_SHOW_ALL_FILTER_LABEL = "- Select a Filter (Showing All) -"


class FolderFilters(QWidget, ThemableMixin):
    filters_requested = Signal()
    saved_filter_selection_changed = Signal(bool)
    genre_changed = Signal(object)
    root_folder = Signal(object)
    loading_started = Signal(object)
    edit_filter_requested = Signal(str)

    GENRES = sorted(
        ["Action", "Comedy", "Sci-Fi", "Mystery", "Thriller", "Drama", "Adventure"]
    )

    def __init__(
        self,
        filter_engine_engine: FolderFilterFilter,
        file_util: FileUtil,
        settings: Settings,
        log_util,
    ):
        super().__init__()
        self.log_util = log_util
        self._ui_utils = UIUtils()
        self.settings = settings

        self.clear_search_button = QToolButton(self)
        self.filter_criteria_button = QToolButton(self)
        self.genre_combo = GenreComboWidget(self.GENRES, parent=self)
        self.nav_combo = SelectComboBox(self)
        self.saved_filters_combo = SelectComboBox(self)
        self.genre_combo.setVisible(False)
        self.nav_combo.setVisible(False)
        self._criteria_popup: FilterCriteriaDialog | None = None

        self.media_filter_widget = FolderFilterMedia(self.settings, log_util, self)
        self.filter_table = FolderFilterTable(
            self.GENRES,
            self.settings.settings_data_model.media_configs,
            state=self.settings.settings_data_model,
            tag_store=getattr(self.settings, "tag_store", None),
            readonly=True,
        )
        self.filter_table.setParent(self)

        self.root_folders: list[str] = []
        self.folder_nav_filters_filter = filter_engine_engine
        self.file_util = file_util
        self.db_filter = DbFilter(
            self.settings.settings_data_model,
            getattr(self.file_util, "path_utils", None) or FileUtils(),
        )

    def build(self) -> QWidget:
        filter_container = QWidget(self)

        self.build_nav_combo()
        self._build_saved_filters_combo()
        self._build_filter_criteria_button()
        self._build_clear_search_button()

        # Add saved filters and filter controls row
        saved_filters_layout = QHBoxLayout()
        saved_filters_layout.addWidget(self.saved_filters_combo, 1)
        saved_filters_layout.addWidget(self.filter_criteria_button)
        saved_filters_layout.addWidget(self.clear_search_button)

        filter_layout = QVBoxLayout(filter_container)
        filter_layout.setSpacing(4)
        filter_layout.setContentsMargins(2, 0, 2, 0)
        filter_layout.addWidget(self.media_filter_widget)
        filter_layout.addLayout(saved_filters_layout)

        left_layout = QVBoxLayout(self)
        left_layout.addWidget(filter_container)
        left_layout.setContentsMargins(2, 0, 2, 0)

        self._connect_sigs()
        return self

    def build_nav_combo(self) -> None:
        self.nav_combo.blockSignals(True)
        self.nav_combo.clear()
        self.nav_combo.addItem("- Select Folder -", userData="")
        for config in self.settings.settings_data_model.media_configs:
            label = config.get("label", "")
            if not label:
                label = config.get("path", "")
            self.nav_combo.addItem(label, userData=config["path"])

        self.nav_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.nav_combo.setMinimumHeight(40)
        self.nav_combo.blockSignals(False)

    def _build_clear_search_button(self) -> None:
        self.clear_search_button = self._make_tool_button("Clear Filter", "fa6s.xmark")
        self.clear_search_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly
        )
        self.clear_search_button.setFixedWidth(40)
        self.clear_search_button.setEnabled(False)
        self.clear_search_button.clicked.connect(self._clear_search)

    def _build_filter_criteria_button(self) -> None:
        self.filter_criteria_button = self._make_tool_button(
            "View Filter Criteria", "fa6s.filter"
        )
        self.filter_criteria_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly
        )
        self.filter_criteria_button.setFixedWidth(40)
        self.filter_criteria_button.setEnabled(False)
        self.filter_criteria_button.clicked.connect(self._show_filter_criteria)

    def _build_saved_filters_combo(self) -> None:
        self.saved_filters_combo.setEditable(True)
        self.saved_filters_combo.setToolTip("Select a saved filter (type to search)")
        self.saved_filters_combo.installEventFilter(self)
        line_edit = self.saved_filters_combo.lineEdit()
        if line_edit is not None:
            line_edit.installEventFilter(self)
        self._refresh_saved_filters_combo()
        self.saved_filters_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.saved_filters_combo.setMinimumHeight(35)

    def _refresh_saved_filters_combo(self) -> None:
        selected_name = (
            self.saved_filters_combo.currentData()
            if self.saved_filters_combo.currentIndex() > 0
            else None
        )
        self.saved_filters_combo.blockSignals(True)
        self.saved_filters_combo.clear()
        self.saved_filters_combo.addItem(_SHOW_ALL_FILTER_LABEL, userData="")
        selected_folders = [
            str(path)
            for media_filter in self.media_filter_widget.collect_filters()
            for path in media_filter.get("value", [])
        ]
        saved = sorted(
            self.settings.settings_data_model.saved_filters,
            key=lambda item: str(item.get("name", "")).casefold(),
        )
        for filter_cfg in saved:
            name = str(filter_cfg.get("name", ""))
            if not name:
                continue
            store = getattr(self.settings.settings_data_model, "filter_store", None)
            if isinstance(store, DbFilters):
                count = store.get_display_count(name, selected_folders)
            else:
                count = filter_cfg.get("total_count")
            label = f"{name} ({count})" if count is not None else name
            self.saved_filters_combo.addItem(label, userData=name)
        if selected_name:
            selected_index = self.saved_filters_combo.findData(selected_name)
            if selected_index > 0:
                self.saved_filters_combo.setCurrentIndex(selected_index)
        self.saved_filters_combo.blockSignals(False)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        combo = self.saved_filters_combo
        if (
            watched in (combo, combo.lineEdit())
            and event.type() == QEvent.Type.MouseButtonPress
            and combo.currentIndex() == 0
            and combo.currentText() == _SHOW_ALL_FILTER_LABEL
        ):
            combo.setEditText("")
            QTimer.singleShot(0, combo.showPopup)
        return super().eventFilter(watched, event)

    def _resolve_filter_text(self, text: str) -> int:
        """Map typed combo text to a saved-filter item index (-1 when unknown).

        Prefers an exact case-insensitive match; otherwise accepts a unique
        prefix match so typing progressively selects the intended filter.
        """
        wanted = text.strip().casefold()
        if not wanted:
            return -1

        combo = self.saved_filters_combo
        prefix_index = -1
        prefix_matches = 0
        for index in range(combo.count()):
            name = str(combo.itemData(index) or combo.itemText(index)).casefold()
            if name == wanted:
                return index
            if name.startswith(wanted):
                prefix_index = index
                prefix_matches += 1

        return prefix_index if prefix_matches == 1 else -1

    def _handle_filter_text(self, text: str) -> None:
        """Resolve typed filter names into a selection of the saved-filter combo."""
        index = self._resolve_filter_text(text)
        if index < 0 or index == self.saved_filters_combo.currentIndex():
            return
        self.saved_filters_combo.setCurrentIndex(index)

    def _make_tool_button(
        self, label: str, icon_name: str = "fa6s.folder"
    ) -> QToolButton:
        btn = ActionButton(self, icon_name=icon_name, tooltip=label)
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return btn

    def _connect_sigs(self) -> None:
        self.nav_combo.currentIndexChanged.connect(self._handle_media_selection)
        self.media_filter_widget.apply_filters.connect(self.filters_requested.emit)
        self.saved_filters_combo.currentIndexChanged.connect(self._load_saved_filter)
        self.saved_filters_combo.currentTextChanged.connect(self._handle_filter_text)
        self.saved_filters_combo.currentTextChanged.connect(
            self._update_clear_search_enabled
        )
        self.genre_combo.genre_changed.connect(
            lambda payload: self.genre_changed.emit(payload)
        )
        self.filter_table.genre_changed.connect(
            lambda payload: self.genre_changed.emit(payload)
        )
        self.filter_table.root_folder.connect(
            lambda payload: self.root_folder.emit(payload)
        )

        def refresh_all():
            self.build_nav_combo()
            selected_folders = set(
                self.settings.settings_data_model.selected_media_folders
            )
            for button in self.media_filter_widget.media_button_group:
                button_paths = button.property("media_paths") or []
                button.setChecked(
                    any(path in selected_folders for path in button_paths)
                )
            self._on_media_filter_selection_changed()
            # Preserve the currently selected filter name before rebuilding the combo
            current_filter_name = ""
            if self.saved_filters_combo.currentIndex() > 0:
                current_filter_name = str(
                    self.saved_filters_combo.currentData()
                    or self.saved_filters_combo.currentText()
                )
            self._refresh_saved_filters_combo()
            # Restore the selected filter if it still exists
            if current_filter_name:
                restored_index = self.saved_filters_combo.findData(current_filter_name)
                if restored_index > 0:
                    self.saved_filters_combo.setCurrentIndex(restored_index)
                    self._load_saved_filter(restored_index)
                else:
                    # Filter was deleted; clear selection
                    self._load_saved_filter(0)
            else:
                self._load_saved_filter(self.saved_filters_combo.currentIndex())
            self.apply_filters()
            self.filters_requested.emit()

        self.settings.settings_data_model.settings_changed.connect(refresh_all)
        self.settings.settings_data_model.filter_counts_changed.connect(
            self._refresh_saved_filters_combo
        )
        self.media_filter_widget.apply_filters.connect(
            self._on_media_filter_selection_changed
        )

    def _update_clear_search_enabled(self, text: str) -> None:
        """Enable clear button only when search text exists."""
        self.clear_search_button.setEnabled(bool(text.strip()))

    def _clear_search(self) -> None:
        """Clear the saved filters combo search text."""
        line_edit = self.saved_filters_combo.lineEdit()
        if line_edit is not None:
            line_edit.clear()
            line_edit.setFocus()

    def _on_media_filter_selection_changed(self) -> None:
        selected_folders = [
            str(path)
            for media_filter in self.media_filter_widget.collect_filters()
            for path in media_filter.get("value", [])
        ]
        state = self.settings.settings_data_model
        state.selected_media_folders = selected_folders
        state.media_folder_selection_changed.emit(selected_folders)
        self._refresh_saved_filters_combo()

    def _handle_media_selection(self, index: int) -> None:
        if index < 0:
            return

        path_from_settings = self.nav_combo.itemData(index)
        if not path_from_settings:
            return

        payload = SignalPayload(
            data=path_from_settings,
            sender=self.__class__.__name__,
            name="Root Folder Changed",
            description="Emitted when a root folder is selected in FolderFilter.",
            flow=SignalFlow.USER_INPUT,
        )
        self.root_folder.emit(payload)

    def _load_saved_filter(self, index: int) -> None:
        has_filter = index > 0
        self.saved_filter_selection_changed.emit(has_filter)
        # Enable/disable View Filter Criteria button based on selection
        self.filter_criteria_button.setEnabled(has_filter)
        if not has_filter:
            self.filter_table.setRowCount(0)
            self.filter_table._check_empty_state()
            self.filters_requested.emit()
            return

        name = str(
            self.saved_filters_combo.itemData(index)
            or self.saved_filters_combo.itemText(index)
        )
        filters = None
        for f in self.settings.settings_data_model.saved_filters:
            if f.get("name") == name:
                filters = f.get("filters")
                break

        self.filter_table.setRowCount(0)
        if filters:
            for filter_item in filters:
                self.filter_table.add_filter(
                    filter_item["filter"], filter_item["value"]
                )
        self.filter_table._check_empty_state()
        # Auto-apply the filter when selected
        self.filters_requested.emit()

    def clear_saved_filter(self) -> None:
        if self.saved_filters_combo.currentIndex() > 0:
            self.saved_filters_combo.setCurrentIndex(0)

    def _show_filter_criteria(self) -> None:
        if self._criteria_popup is None:
            self._build_filter_criteria_popup()
        if self._criteria_popup is None:
            return

        # Refresh the dialog with current filter data
        self._refresh_criteria_dialog()

        pos = self.filter_criteria_button.mapToGlobal(
            self.filter_criteria_button.rect().bottomLeft()
        )
        screen = self.screen()
        if screen is not None:
            available = screen.availableGeometry()
            popup_w = min(520, available.width() - 20)
            popup_h = min(420, available.height() - 20)
            self._criteria_popup.resize(popup_w, popup_h)
            x = min(pos.x(), available.right() - popup_w - 10)
            y = min(pos.y(), available.bottom() - popup_h - 10)
            self._criteria_popup.move(max(x, available.left()), max(y, available.top()))
        else:
            self._criteria_popup.resize(520, 420)
            self._criteria_popup.move(pos)
        self._criteria_popup.show()
        self._criteria_popup.raise_()
        self._criteria_popup.activateWindow()

    def _refresh_criteria_dialog(self) -> None:
        """Update the criteria dialog with the currently selected filter's data."""
        if self._criteria_popup is None:
            return
        index = self.saved_filters_combo.currentIndex()
        filter_name = ""
        filters: list[dict[str, str]] = []
        if index > 0:
            filter_name = str(
                self.saved_filters_combo.itemData(index)
                or self.saved_filters_combo.itemText(index)
            )
            for f in self.settings.settings_data_model.saved_filters:
                if f.get("name") == filter_name:
                    filters = f.get("filters", [])
                    break
        self._criteria_popup.set_filter_data(filter_name, filters)
        # Refresh theme after data change
        self._criteria_popup.apply_theme()

    def _build_filter_criteria_popup(self) -> None:
        # Determine current filter name and criteria
        index = self.saved_filters_combo.currentIndex()
        filter_name = ""
        filters: list[dict[str, str]] = []
        if index > 0:
            filter_name = str(
                self.saved_filters_combo.itemData(index)
                or self.saved_filters_combo.itemText(index)
            )
            for f in self.settings.settings_data_model.saved_filters:
                if f.get("name") == filter_name:
                    filters = f.get("filters", [])
                    break

        dialog = FilterCriteriaDialog(
            genres=self.GENRES,
            media_configs=self.settings.settings_data_model.media_configs,
            tags=self.settings.settings_data_model.tags,
            tag_store=getattr(self.settings, "tag_store", None),
            state=self.settings.settings_data_model,
            filter_name=filter_name,
            filters=filters,
            edit_mode=False,
            readonly=True,
            parent=self.window(),
        )
        # Use Popup window type to match original behavior
        dialog.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.WindowStaysOnTopHint)
        # Wire the dialog's edit_requested signal to emit our edit_filter_requested
        dialog.edit_requested.connect(self.edit_filter_requested.emit)
        self._criteria_popup = dialog

    def apply_filters(
        self,
        selected_folders: list[str] | None = None,
        on_complete: Callable[[list[FileUtilModel]], None] | None = None,
    ) -> None:
        # Collect items from all configured roots: explicit selection takes
        # precedence, otherwise gather from all root_folders.
        items: list[FileUtilModel] = []

        # Gather items from all configured root folders
        if selected_folders:
            folder_paths = selected_folders
        else:
            folder_paths = [
                config["path"]
                for config in self.settings.settings_data_model.media_configs
                if config.get("path")
            ]

        if self.settings.settings_data_model.db_enabled():
            # Use fast vectorized database filtering
            for folder_path in folder_paths:
                self.loading_started.emit([folder_path])

            filters = self.filter_table.collect_filters()
            filters.extend(self.media_filter_widget.collect_filters())

            results = self.db_filter.filter(
                filters=filters,
                selected_folders=folder_paths,
            )
            if on_complete:
                on_complete(results)
            return

        # Sequential processing helper
        def run_scan(index: int):
            if index >= len(folder_paths):
                if on_complete:
                    on_complete(self._apply_filters_internal(items))
                return

            folder_path = folder_paths[index]
            if not folder_path:
                run_scan(index + 1)
                return

            self.loading_started.emit([folder_path])

            def folder_scanned(path_items: list[FileUtilModel]):
                items.extend(path_items)
                run_scan(index + 1)

            self.file_util.get_files_from_path_async(
                folder_path, on_complete=folder_scanned
            )

        run_scan(0)

    def _apply_filters_internal(
        self, items: list[FileUtilModel]
    ) -> list[FileUtilModel]:
        filters = self.filter_table.collect_filters()

        # Add active media buttons to filters
        filters.extend(self.media_filter_widget.collect_filters())

        return self.folder_nav_filters_filter.apply_filters(
            items=items,
            filters=filters,
        )

    def apply_theme(self) -> None:
        super().apply_theme()
