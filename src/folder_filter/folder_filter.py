from __future__ import annotations

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.folder_filter.folder_filter_media import FolderFilterMedia
from src.folder_filter.folder_filter_table import FolderFilterTable
from src.folder_filter.folder_filter_filter import FolderFilterFilter
from src.settings.settings import Settings
from src.theme.theme import APP_THEME
from src.utils.file_util import FileUtil
from src.utils.file_util_model import FileUtilModel
from src.widgets.base_widget import BaseWidget


class FolderFilters(BaseWidget):
    sig_apply_filters = Signal()
    sig_genre_changed = Signal(str)
    sig_root_folder = Signal(str)

    GENRES = sorted(
        ["Action", "Comedy", "Sci-Fi", "Mystery", "Thriller", "Drama", "Adventure"]
    )

    def __init__(
        self,
        folder_filter_engine: FolderFilterFilter,
        file_util: FileUtil,
        settings: Settings,
        log_util,
    ):
        super().__init__(log_util)
        self.settings = settings
        self.apply_button = QToolButton()
        self.add_filter_button = QToolButton()
        self.filter_type_combo = QComboBox()
        self.genre_combo = QComboBox()
        self.nav_combo = QComboBox()
        self.saved_filters_combo = QComboBox()
        self.save_filter_button = QToolButton()
        # self.delete_filter_button = QToolButton()
        self.media_filter = FolderFilterMedia(self.settings, self)
        self.filter_table = FolderFilterTable(self.GENRES, self.settings.settings_data_model.folder_configs)
        # support multiple roots
        self.root_folders: list[str] = []
        self.folder_nav_filters_filter = folder_filter_engine
        self.file_util = file_util

    def build(self) -> QWidget:
        filter_container = QWidget()
        filter_container.setStyleSheet(APP_THEME.container_qss())

        self._build_genre_combo()
        self.build_nav_combo()
        self._build_filter_type_combo()
        self._build_apply_button()
        self._build_add_filter_button()
        self._build_saved_filters_combo()
        self._build_save_filter_button()
        # self._build_delete_filter_button()

        self.filter_table = FolderFilterTable(self.GENRES, self.settings.settings_data_model.folder_configs)

        buttons_to_style = [
            self.apply_button,
            self.add_filter_button,
            self.save_filter_button,
            # self.delete_filter_button,
        ]

        for button in buttons_to_style:
            button.setStyleSheet(APP_THEME.button_qss())

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
        filter_layout.addWidget(self.media_filter)
        filter_layout.addLayout(saved_filters_layout)
        filter_layout.addLayout(add_filter_layout)
        filter_layout.addWidget(self.filter_table)

        left_layout = QVBoxLayout(self)
        left_layout.addWidget(filter_container)

        self._connect_sigs()
        return self

    def _build_genre_combo(self) -> None:
        self.genre_combo = QComboBox()
        self.genre_combo.addItem("-none-")
        for genre in self.GENRES:
            self.genre_combo.addItem(genre)

    def build_nav_combo(self) -> None:
        self.nav_combo = QComboBox()
        self.nav_combo.clear()
        self.nav_combo.addItem("- Select Folder -", userData="")
        for config in self.settings.settings_data_model.folder_configs:
            label = config["label"]
            self.nav_combo.addItem(label, userData=config["path"])

        self.nav_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.nav_combo.setMinimumHeight(40)

    def _build_filter_type_combo(self) -> None:
        self.filter_type_combo = QComboBox()
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
        self.apply_button = self._make_tool_button("Apply Filters", "fa5s.sync-alt")
        self.apply_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.apply_button.setFixedWidth(60)

    def _build_add_filter_button(self) -> None:
        self.add_filter_button = self._make_tool_button(
            "Add Filter", "fa5s.plus-circle"
        )
        self.add_filter_button.setFixedWidth(60)

    def _build_saved_filters_combo(self) -> None:
        self.saved_filters_combo = QComboBox()
        self.saved_filters_combo.setEditable(True)
        self.saved_filters_combo.lineEdit().setPlaceholderText("- Select Saved Filters -")
        self._refresh_saved_filters_combo()
        self.saved_filters_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.saved_filters_combo.setMinimumHeight(40)

    def _refresh_saved_filters_combo(self) -> None:
        self.saved_filters_combo.clear()
        self.saved_filters_combo.addItem("")
        filter_names = [f.get("name") for f in self.settings.settings_data_model.saved_filters]
        for name in sorted(filter_names):
            self.saved_filters_combo.addItem(name)

    def _build_save_filter_button(self) -> None:
        self.save_filter_button = self._make_tool_button("Save Filter", "fa5s.save")
        self.save_filter_button.setFixedWidth(60)

    def _build_delete_filter_button(self) -> None:
        pass
        # self.delete_filter_button = self._make_tool_button(
        #     "Delete Filter", "edit-delete"
        # )
        # self.delete_filter_button.setFixedWidth(60)

    def _make_tool_button(
        self, label: str, icon_name: str = "fa5s.folder"
    ) -> QToolButton:
        btn = QToolButton()
        btn.setToolTip(label)
        # btn.setText(label)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        btn.setIcon(APP_THEME.icon(icon_name, color=APP_THEME.text_color))
        btn.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
        # btn.setText(f"  {label}")
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setMaximumWidth(300)
        return btn

    def _connect_sigs(self) -> None:
        self.apply_button.clicked.connect(self.sig_apply_filters.emit)
        self.media_filter.sig_apply_filters.connect(self.sig_apply_filters.emit)
        self.add_filter_button.clicked.connect(self._add_filter_clicked)
        self.save_filter_button.clicked.connect(self._save_filter_clicked)
        # self.delete_filter_button.clicked.connect(self._delete_filter_clicked)
        self.saved_filters_combo.currentIndexChanged.connect(self._load_saved_filter)
        self.genre_combo.currentTextChanged.connect(self.sig_genre_changed.emit)
        self.nav_combo.currentIndexChanged.connect(self._handle_media_selection)
        self.filter_table.sig_genre_changed.connect(self.sig_genre_changed.emit)
        self.filter_table.sig_root_folder.connect(self.sig_root_folder.emit)

        def refresh_all():
            self.build_nav_combo()
            self._refresh_saved_filters_combo()

        self.settings.settings_data_model.sig_settings_changed.connect(refresh_all)

    def _handle_media_selection(self, index: int) -> None:
        if index < 0:
            return

        path_from_settings = self.nav_combo.itemData(index)
        if not path_from_settings:
            return

        self.sig_root_folder.emit(path_from_settings)

    def _add_filter_clicked(self) -> None:
        filter_type = self.filter_type_combo.currentText().strip()
        if filter_type.upper() in ("", "OS", "NFO"):
            return

        self.filter_table.add_filter(filter_type)

        filter_name = self.saved_filters_combo.currentText().strip()
        if filter_name == "":
            self.saved_filters_combo.lineEdit().setPlaceholderText("NameThisFilter")

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
            self.saved_filters_combo.lineEdit().setPlaceholderText("- Select Saved Filters -")
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
    ) -> list[FileUtilModel]:
        # Collect items from all configured roots: explicit selection takes
        # precedence, otherwise gather from all root_folders.
        items: list[FileUtilModel] = []

        # Gather items from all configured root folders
        if selected_folders:
            folder_paths = selected_folders
        else:
            folder_paths = self.root_folders

        # print(f"apply_filters: folder_paths: {folder_paths}")

        for folder_path in folder_paths:
            if folder_path:
                items.extend(self.file_util.get_files_from_path(folder_path))
        filters = self.filter_table.collect_filters()

        # Add active media buttons to filters
        filters.extend(self.media_filter.collect_filters())

        return self.folder_nav_filters_filter.apply_filters(
            items=items,
            filters=filters,
        )

    def apply_theme(self) -> None:
        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.setStyleSheet(APP_THEME.container_qss())

        APP_THEME.setup_combo_box(self.filter_type_combo)
        APP_THEME.setup_combo_box(self.genre_combo)
        APP_THEME.setup_combo_box(self.nav_combo)
        APP_THEME.setup_combo_box(self.saved_filters_combo)

        if self.filter_table is not None:
            self.filter_table.apply_theme()
