from __future__ import annotations

import os
import duckdb
from collections.abc import Callable

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
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
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.ui_utils import UIUtils


class FolderFilters(QWidget, ThemableMixin):
    filters_requested = Signal()
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
        # Create child widgets with explicit parent to avoid becoming top-level windows
        # TODO these are rebuilt using _make_tool_button, declare instead of init
        self.apply_button = QToolButton(self)
        self.add_filter_button = QToolButton(self)
        self.filter_type_combo = QComboBox(self)
        self.genre_combo = GenreComboWidget(self.GENRES, parent=self)
        self.nav_combo = QComboBox(self)
        self.saved_filters_combo = QComboBox(self)
        self.save_filter_button = QToolButton(self)
        # These are helper controls kept for signal plumbing / future reuse. They
        # are intentionally hidden because the actual filter editors live inside the
        # table rows and should not duplicate at the top-left of the app.
        self.genre_combo.setVisible(False)
        self.nav_combo.setVisible(False)
        # self.saved_filters_combo.setVisible(False)
        self.save_filter_button.setVisible(False)
        # self.filter_type_combo.setVisible(False)
        self.add_filter_button.setVisible(False)
        self.apply_button.setVisible(False)
        # self.delete_filter_button = QToolButton(self)
        self.media_filter_widget = FolderFilterMedia(self.settings, log_util, self)
        self.filter_table = FolderFilterTable(
            self.GENRES, self.settings.settings_data_model.media_configs
        )
        # support multiple roots
        self.root_folders: list[str] = []
        self.folder_nav_filters_filter = filter_engine_engine
        self.file_util = file_util

    def build(self) -> QWidget:
        filter_container = QWidget(self)

        self.build_nav_combo()
        self._build_filter_type_combo()
        self._build_apply_button()
        self._build_add_filter_button()
        self._build_saved_filters_combo()
        self._build_save_filter_button()
        # self._build_delete_filter_button()

        self.filter_table = FolderFilterTable(
            self.GENRES, self.settings.settings_data_model.media_configs
        )

        # Add filter controls row
        add_filter_layout = QHBoxLayout()
        add_filter_layout.addWidget(self.filter_type_combo)
        add_filter_layout.addWidget(self.add_filter_button)
        add_filter_layout.addWidget(self.apply_button)

        # Add saved filters row
        saved_filters_layout = QHBoxLayout()
        saved_filters_layout.addWidget(self.saved_filters_combo)
        saved_filters_layout.addWidget(self.save_filter_button)
        # saved_filters_layout.addWidget(self.delete_filter_button)

        filter_layout = QVBoxLayout(filter_container)
        filter_layout.setSpacing(0)
        filter_layout.setContentsMargins(2, 0, 2, 0)
        filter_layout.addWidget(self.media_filter_widget)
        filter_layout.addLayout(saved_filters_layout)
        filter_layout.addLayout(add_filter_layout)
        filter_layout.addWidget(self.filter_table)

        left_layout = QVBoxLayout(self)
        left_layout.addWidget(filter_container)
        # for debug, move filters down 2, 30, 2, 0
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

    def _build_filter_type_combo(self) -> None:
        # self.filter_type_combo = QComboBox(self)
        self.filter_type_combo.setEditable(True)
        index = 0
        for filter_type in FolderFilterTable.FILTER_TYPES:
            clean_type = filter_type.casefold().strip()
            if clean_type in ("os", "nfo"):
                self.filter_type_combo.insertSeparator(index)
                label_text = filter_type
                self.filter_type_combo.addItem(label_text)
                # Disable OS and NFO so they act as headers
                model = self.filter_type_combo.model()
                model_index = model.index(index + 1, 0)
                model.setData(model_index, 0, Qt.ItemDataRole.UserRole - 1)
                index += 1
            else:
                label_text = f"  {filter_type}"
                self.filter_type_combo.addItem(label_text)
            index += 1
        self.filter_type_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

    def _build_apply_button(self) -> None:
        self.apply_button = self._make_tool_button("Apply Filters", "fa6s.rotate")
        self.apply_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.apply_button.setFixedWidth(50)

    def _build_add_filter_button(self) -> None:
        self.add_filter_button = self._make_tool_button(
            "Add Filter", "fa6s.circle-plus"
        )
        self.add_filter_button.setFixedWidth(50)

    def _build_saved_filters_combo(self) -> None:
        # self.saved_filters_combo = QComboBox(self)
        self.saved_filters_combo.setEditable(True)
        line_edit = self.saved_filters_combo.lineEdit()
        if line_edit is not None:
            line_edit.setPlaceholderText("- Select Saved Filters -")
        self._refresh_saved_filters_combo()
        self.saved_filters_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.saved_filters_combo.setMinimumHeight(40)

    def _refresh_saved_filters_combo(self) -> None:
        self.saved_filters_combo.clear()
        self.saved_filters_combo.addItem("")
        filter_names = [
            f.get("name", "") for f in self.settings.settings_data_model.saved_filters
        ]
        for name in sorted(filter_names):
            self.saved_filters_combo.addItem(name)

    def _build_save_filter_button(self) -> None:
        self.save_filter_button = self._make_tool_button("Save Filter", "fa6s.floppy-disk")
        self.save_filter_button.setFixedWidth(50)

    def _build_delete_filter_button(self) -> None:
        pass
        # self.delete_filter_button = self._make_tool_button(
        #     "Delete Filter", "edit-delete"
        # )
        # self.delete_filter_button.setFixedWidth(60)

    def _make_tool_button(
        self, label: str, icon_name: str = "fa6s.folder"
    ) -> QToolButton:
        btn = QToolButton(self)
        btn.setToolTip(label)
        # btn.setText(label)
        # btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        btn.setIcon(APP_THEME.icon(icon_name, color=APP_THEME.text_color))
        btn.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
        # btn.setText(f"  {label}")
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setMaximumWidth(300)
        return btn

    def _connect_sigs(self) -> None:
        self.nav_combo.currentIndexChanged.connect(self._handle_media_selection)
        self.apply_button.clicked.connect(self.filters_requested.emit)
        self.media_filter_widget.apply_filters.connect(self.filters_requested.emit)
        self.add_filter_button.clicked.connect(self._add_filter_clicked)
        self.save_filter_button.clicked.connect(self._save_filter_clicked)
        # self.delete_filter_button.clicked.connect(self._delete_filter_clicked)
        self.saved_filters_combo.currentIndexChanged.connect(self._load_saved_filter)
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

    def _add_filter_clicked(self) -> None:
        filter_type = self.filter_type_combo.currentText().strip()
        if filter_type.upper() in ("", "OS", "NFO"):
            return

        self.filter_table.add_filter(filter_type)

        filter_name = self.saved_filters_combo.currentText().strip()
        if filter_name == "":
            line_edit = self.saved_filters_combo.lineEdit()
            if line_edit:
                line_edit.setPlaceholderText("Name This Filter")

    def _save_filter_clicked(self) -> None:
        filters = self.filter_table.collect_filters()
        if not filters:
            return

        name = self.saved_filters_combo.currentText()
        if name and name != "":
            self.settings.save_filter(name, filters)

    def _delete_filter_clicked(self) -> None:
        index = self.saved_filters_combo.currentIndex()
        if index <= 0:
            line_edit = self.saved_filters_combo.lineEdit()
            if line_edit is not None:
                line_edit.setPlaceholderText("- Select Saved Filters -")
            return

        name = self.saved_filters_combo.currentText()
        self.settings.delete_filter(name)

    def _load_saved_filter(self, index: int) -> None:
        if index <= 0:
            return

        name = self.saved_filters_combo.itemText(index)
        filters = None
        for f in self.settings.settings_data_model.saved_filters:
            if f.get("name") == name:
                filters = f.get("filters")
                break

        if not filters:
            return

        self.filter_table.setRowCount(0)
        self.filter_table._check_empty_state()
        for filter_item in filters:
            self.filter_table.add_filter(filter_item["filter"], filter_item["value"])

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
            folder_paths = [config["path"] for config in self.settings.settings_data_model.media_configs if config.get("path")]

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

                if db_path and os.path.exists(db_path):
                    con = duckdb.connect(db_path)
                    res = con.execute(db_query.DbQuery.MediaFile.SELECT_ALL_PATHS).fetchall()
                    con.close()

                    # 1. Add files and their parent directories
                    paths = [r[0] for r in res]
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

        return self.folder_nav_filters_filter.apply_filters(
            items=items,
            filters=filters,
        )

    def apply_theme(self) -> None:
        super().apply_theme()
