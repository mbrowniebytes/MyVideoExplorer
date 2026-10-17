from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import duckdb
from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLayout,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.db import db_query
from MyVideoExplorer.folder_filter.folder_filter_filter import FolderFilterFilter
from MyVideoExplorer.folder_filter.folder_filter_genre_combo_widget import (
    GenreComboWidget,
)
from MyVideoExplorer.folder_filter.folder_filter_media import FolderFilterMedia
from MyVideoExplorer.folder_filter.folder_filter_table import FolderFilterTable
from MyVideoExplorer.settings.settings import Settings
from MyVideoExplorer.tag_cloud.tag_button import TagButton
from MyVideoExplorer.tag_cloud.tag_picker_dialog import TagPickerDialog
from MyVideoExplorer.tag_cloud.tag_util import get_contrast_text_color
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.ui_utils import UIUtils
from MyVideoExplorer.widgets.flow_layout import FlowLayout


class FolderFilters(QWidget, ThemableMixin):
    filters_requested = Signal()
    saved_filter_selection_changed = Signal(bool)
    genre_changed = Signal(object)
    root_folder = Signal(object)
    loading_started = Signal(object)

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

        self.apply_button = QToolButton(self)
        self.tag_button = QToolButton(self)
        self.filter_criteria_button = QToolButton(self)
        self.genre_combo = GenreComboWidget(self.GENRES, parent=self)
        self.nav_combo = QComboBox(self)
        self.saved_filters_combo = QComboBox(self)
        self.selected_tags_container = QWidget(self)
        self.selected_tags_layout = FlowLayout(self.selected_tags_container, spacing=4)

        self.genre_combo.setVisible(False)
        self.nav_combo.setVisible(False)
        self.selected_tags_container.setVisible(False)

        self._selected_tags: list[str] = []
        self._popup: TagPickerDialog | None = None
        self._criteria_popup: QDialog | None = None

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

    @property
    def selected_tags(self) -> list[str]:
        return list(self._selected_tags)

    def build(self) -> QWidget:
        filter_container = QWidget(self)

        self.build_nav_combo()
        self._build_saved_filters_combo()
        self._build_filter_criteria_button()
        self._build_tag_button()
        self._build_apply_button()

        # Add saved filters and filter controls row
        saved_filters_layout = QHBoxLayout()
        saved_filters_layout.addWidget(self.saved_filters_combo, 1)
        saved_filters_layout.addWidget(self.filter_criteria_button)
        saved_filters_layout.addWidget(self.tag_button)
        saved_filters_layout.addWidget(self.apply_button)

        filter_layout = QVBoxLayout(filter_container)
        filter_layout.setSpacing(4)
        filter_layout.setContentsMargins(2, 0, 2, 0)
        filter_layout.addWidget(self.media_filter_widget)
        filter_layout.addLayout(saved_filters_layout)
        filter_layout.addWidget(self.selected_tags_container)

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

    def _build_apply_button(self) -> None:
        self.apply_button = self._make_tool_button("Apply Filters", "fa6s.rotate")
        self.apply_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.apply_button.setFixedWidth(40)

    def _build_tag_button(self) -> None:
        self.tag_button = self._make_tool_button("Tags", "fa6s.tag")
        self.tag_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.tag_button.setFixedWidth(40)
        self.tag_button.clicked.connect(self._show_tag_cloud)

    def _build_filter_criteria_button(self) -> None:
        self.filter_criteria_button = self._make_tool_button(
            "View Filter Criteria", "fa6s.filter"
        )
        self.filter_criteria_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly
        )
        self.filter_criteria_button.setFixedWidth(40)
        self.filter_criteria_button.clicked.connect(self._show_filter_criteria)

    def _build_saved_filters_combo(self) -> None:
        self.saved_filters_combo.setEditable(True)
        self.saved_filters_combo.setToolTip(
            "Select a saved filter (type to search)"
        )
        self._refresh_saved_filters_combo()
        self.saved_filters_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.saved_filters_combo.setMinimumHeight(35)

    def _refresh_saved_filters_combo(self) -> None:
        self.saved_filters_combo.blockSignals(True)
        self.saved_filters_combo.clear()
        self.saved_filters_combo.addItem("- Showing All - Select a Filter -")
        filter_names = [
            f.get("name", "")
            for f in self.settings.settings_data_model.saved_filters
            if f.get("name")
        ]
        for name in sorted(filter_names):
            self.saved_filters_combo.addItem(name)
        self.saved_filters_combo.blockSignals(False)

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
            name = combo.itemText(index).casefold()
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
        btn = QToolButton(self)
        btn.setToolTip(label)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        btn.setIcon(APP_THEME.icon(icon_name, color=APP_THEME.text_color))
        btn.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        btn.setAutoRaise(True)
        return btn

    def _connect_sigs(self) -> None:
        self.nav_combo.currentIndexChanged.connect(self._handle_media_selection)
        self.apply_button.clicked.connect(self.filters_requested.emit)
        self.media_filter_widget.apply_filters.connect(self.filters_requested.emit)
        self.saved_filters_combo.currentIndexChanged.connect(self._load_saved_filter)
        self.saved_filters_combo.currentTextChanged.connect(self._handle_filter_text)
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
            self._refresh_saved_filters_combo()
            self._load_saved_filter(self.saved_filters_combo.currentIndex())
            self.apply_filters()
            self.filters_requested.emit()

        self.settings.settings_data_model.settings_changed.connect(refresh_all)

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
        self.saved_filter_selection_changed.emit(index > 0)
        self.clear_selected_tags()
        if index <= 0:
            self.filter_table.setRowCount(0)
            self.filter_table._check_empty_state()
            return

        name = self.saved_filters_combo.itemText(index)
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

    def clear_saved_filter(self) -> None:
        if self.saved_filters_combo.currentIndex() > 0:
            self.saved_filters_combo.setCurrentIndex(0)

    def _show_filter_criteria(self) -> None:
        if self._criteria_popup is None:
            self._build_filter_criteria_popup()
        assert self._criteria_popup is not None

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
            self._criteria_popup.move(
                max(x, available.left()), max(y, available.top())
            )
        else:
            self._criteria_popup.resize(520, 420)
            self._criteria_popup.move(pos)
        self._criteria_popup.show()
        self._criteria_popup.raise_()
        self._criteria_popup.activateWindow()

    def _build_filter_criteria_popup(self) -> None:
        popup = QDialog(self.window())
        popup.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.WindowStaysOnTopHint
        )
        popup.setWindowTitle("Filter Criteria")
        popup.setStyleSheet(APP_THEME.container_qss())
        popup.resize(520, 420)
        popup.setMinimumSize(450, 300)

        layout = QVBoxLayout(popup)
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Filter Criteria", popup))
        header_layout.addStretch(1)

        close_button = QToolButton(popup)
        close_button.setIcon(
            APP_THEME.icon("fa6s.xmark", color=APP_THEME.text_color)
        )
        close_button.setIconSize(QSize(14, 14))
        close_button.setFixedSize(22, 22)
        close_button.setAutoRaise(True)
        close_button.setToolTip("Close")
        close_button.clicked.connect(popup.close)
        header_layout.addWidget(close_button)
        layout.addLayout(header_layout)

        scroll = QScrollArea(popup)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.filter_table)
        layout.addWidget(scroll, 1)
        self._criteria_popup = popup

    def _show_tag_cloud(self) -> None:
        if self._popup is None:
            self._build_popup()
        self._sync_popup_data()
        assert self._popup is not None
        pos = self.tag_button.mapToGlobal(self.tag_button.rect().bottomLeft())
        screen = self.screen()
        if screen is not None:
            available = screen.availableGeometry()
            popup_w = min(
                max(520, self._popup.sizeHint().width()), available.width() - 20
            )
            popup_h = min(
                max(420, self._popup.sizeHint().height()), available.height() - 20
            )
            self._popup.resize(popup_w, popup_h)
            x = min(pos.x(), available.right() - self._popup.width() - 10)
            y = min(pos.y(), available.bottom() - self._popup.height() - 10)
            self._popup.move(max(x, available.left()), max(y, available.top()))
        else:
            self._popup.resize(520, 420)
            self._popup.move(pos)
        self._popup.show()
        self._popup.raise_()
        self._popup.activateWindow()

    def _build_popup(self) -> None:
        owner = self.window()
        self._popup = TagPickerDialog(owner, allow_create=False, allow_delete=False)
        self._popup.tag_selected.connect(self._on_tag_selected)
        self._popup.tag_created.connect(self._on_tag_created)

    def _sync_popup_data(self) -> None:
        if self._popup is None:
            return
        tag_store = getattr(self.settings, "tag_store", None)
        catalog_tags = (
            tag_store.list_tags()
            if tag_store
            else (self.settings.settings_data_model.tags if self.settings else [])
        )
        tag_colors = {
            item["tag"].casefold(): item.get("color", "#808080")
            for item in catalog_tags
            if isinstance(item, dict) and "tag" in item
        }
        counts = tag_store.get_tag_counts() if tag_store else {}
        self._popup.set_data(self._selected_tags, tag_colors, catalog_tags, counts)

    def _on_tag_selected(self, tag: str) -> None:
        self.add_selected_tag(tag)
        if self._popup is not None:
            self._popup.close()

    def _on_tag_created(self, tag: str) -> None:
        if not tag:
            return
        tag_store = getattr(self.settings, "tag_store", None)
        if tag_store is not None:
            tag_store.add_catalog_tag(tag)
        elif self.settings and self.settings.settings_data_model:
            self.settings.settings_data_model.add_tag(tag)
        self.add_selected_tag(tag)
        if self._popup is not None:
            self._popup.close()

    def add_selected_tag(self, tag: str) -> None:
        if not tag:
            return
        if tag.casefold() not in {t.casefold() for t in self._selected_tags}:
            self._selected_tags.append(tag)
            self._render_selected_tags()

    def remove_selected_tag(self, tag: str) -> None:
        self._selected_tags = [
            t for t in self._selected_tags if t.casefold() != tag.casefold()
        ]
        self._render_selected_tags()

    def clear_selected_tags(self) -> None:
        self._selected_tags.clear()
        self._render_selected_tags()

    def _render_selected_tags(self) -> None:
        self._clear_layout(self.selected_tags_layout)
        if not self._selected_tags:
            self.selected_tags_container.setVisible(False)
            return

        self.selected_tags_container.setVisible(True)
        tag_store = getattr(self.settings, "tag_store", None)
        catalog_tags = (
            tag_store.list_tags()
            if tag_store
            else (self.settings.settings_data_model.tags if self.settings else [])
        )
        tag_colors = {
            item["tag"].casefold(): item.get("color", "#808080")
            for item in catalog_tags
            if isinstance(item, dict) and "tag" in item
        }
        counts = (
            tag_store.get_tag_counts()
            if tag_store and hasattr(tag_store, "get_tag_counts")
            else {}
        )
        for tag in self._selected_tags:
            color = tag_colors.get(tag.casefold(), "#808080")
            count = counts.get(tag.casefold(), 0)
            btn = TagButton(self.selected_tags_container)
            btn.setText(f"{tag} ({count})  ✕")
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            btn.setToolTip(f"Remove tag filter '{tag}'")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QToolButton {{ color: {get_contrast_text_color(color)}; "
                f"background-color: {color}; border-radius: 4px; padding: 2px 6px; font-weight: bold; }}"
            )
            btn.clicked.connect(lambda _, t=tag: self.remove_selected_tag(t))
            btn.show()
            self.selected_tags_layout.addWidget(btn)

        target_w = self.selected_tags_container.width()
        parent = self.parentWidget()
        if target_w <= 50 and parent is not None:
            target_w = parent.width()
        if target_w <= 50:
            target_w = 200
        target_h = self.selected_tags_layout.heightForWidth(max(target_w, 50))
        self.selected_tags_layout.setGeometry(QRect(0, 0, max(target_w, 50), target_h))
        self.selected_tags_container.updateGeometry()

    @staticmethod
    def _clear_layout(layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget() if item else None
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

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
            # Use database
            for folder_path in folder_paths:
                self.loading_started.emit([folder_path])
                # Find folder config
                db_path = None
                for config in self.settings.settings_data_model.media_configs:
                    if config["path"] == folder_path:
                        db_path = self.settings.settings_data_model.get_db_path(config)
                        break

                if db_path and Path(db_path).exists():
                    db_path_str = Path(db_path).as_posix()
                    con = duckdb.connect(db_path_str)
                    res = con.execute(
                        db_query.DbQuery.MediaFile.SELECT_ALL_PATHS
                    ).fetchall()
                    con.close()

                    # 1. Add files and their parent directories
                    paths = [r[0] for r in res]
                    # Sort by parent folder then filename to mimic filesystem scan order
                    paths.sort(
                        key=lambda p: (
                            str(Path(p).parent).lower(),
                            Path(p).name.lower(),
                        )
                    )
                    h = self.file_util.build_hierarchy_from_paths(paths, folder_path)
                    items.extend(h)

            if on_complete:
                on_complete(self._apply_filters_internal(items))
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

        # Add selected tags to filters
        for tag in self._selected_tags:
            filters.append({"filter": "Tag", "value": tag})

        return self.folder_nav_filters_filter.apply_filters(
            items=items,
            filters=filters,
        )

    def apply_theme(self) -> None:
        super().apply_theme()
