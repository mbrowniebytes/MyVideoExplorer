from typing import Any
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.folder_filter.folder_filter_table import FolderFilterTable

from MyVideoExplorer.settings.settings import SettingsBaseTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil


class SettingsFilterTab(SettingsBaseTab):
    # TODO centralize w/ folder_filter
    GENRES = sorted(
        ["Action", "Comedy", "Sci-Fi", "Mystery", "Thriller", "Drama", "Adventure"]
    )

    def __init__(self, state: SettingsState, log_util: LogUtil, parent: QWidget | None = None) -> None:
        super().__init__(log_util, parent)
        self.state = state
        self.row_widgets: list[QWidget] = []

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.main_widget = QWidget()
        self.content_layout = QVBoxLayout(self.main_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(15)

        self._build_ui()
        self.content_layout.addStretch()

        scroll.setWidget(self.main_widget)
        self.layout.addWidget(scroll)

    def _build_ui(self) -> None:
        self.filter_group = QGroupBox("Saved Filters")
        self.filter_layout = QVBoxLayout(self.filter_group)

        self._refresh_filters()

        self.content_layout.addWidget(self.filter_group)
        self.content_layout.addStretch(2)

        # Move Save Filters Settings button to bottom-right, centered
        save_btn_container = QWidget()
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.save_btn = QPushButton("Save Filter Settings")
        self.save_btn.setFixedWidth(180)
        self.save_btn.clicked.connect(self._save_filter_settings)

        self.reset_btn = self._build_reset_button("Reset Filter Settings", self.reset_settings)
        self.reset_btn.setFixedWidth(180)

        spacer = QWidget()
        spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        save_btn_layout.addWidget(self.reset_btn)
        save_btn_layout.addWidget(spacer)
        save_btn_layout.addWidget(self.save_btn)
        self.content_layout.addWidget(
            save_btn_container,
            alignment=Qt.AlignmentFlag.AlignBottom,
        )

    def reset_settings(self) -> None:
        """Reset settings for this tab."""
        self.state.load_filters()
        self._refresh_filters()
        self.reset_save_button()
        self.sig_saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Filter Settings Reset",
                description="Filter settings were reset to defaults.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        print("Filters Settings reset")


    def _refresh_filters(self) -> None:
        # Clear existing filter rows
        self.row_widgets = []
        while self.filter_layout.count():
            child = self.filter_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.state.saved_filters:
            self.filter_layout.addWidget(QLabel("No saved filters found."))
            return

        for filter_cfg in self.state.saved_filters:
            row_widget = self._make_filter_row(filter_cfg)
            self.row_widgets.append(row_widget)
            self.filter_layout.addWidget(row_widget)

    def _make_filter_row(self, filter_cfg: dict[str, Any]) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        name_container = QWidget()
        name_layout = QHBoxLayout(name_container)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(5)
        layout.addWidget(name_container)

        name_edit = QLineEdit(filter_cfg.get("name", ""))
        name_edit.setPlaceholderText("Filter Name")
        name_edit.textChanged.connect(self._on_setting_changed)
        name_layout.addWidget(name_edit)

        # Filter type combo
        filter_type_combo = QComboBox()
        filter_type_combo.setEditable(True)
        index = 0
        for filter_type in FolderFilterTable.FILTER_TYPES:
            clean_type = filter_type.casefold().strip()
            if clean_type in ("os", "nfo"):
                filter_type_combo.insertSeparator(index)
                label_text = filter_type
                filter_type_combo.addItem(label_text)
                # Disable OS and NFO so they act as headers
                model = filter_type_combo.model()
                model_index = model.index(index + 1, 0)
                model.setData(model_index, 0, Qt.ItemDataRole.UserRole - 1)
                index += 1
            else:
                label_text = f"  {filter_type}"
                filter_type_combo.addItem(label_text)
            index += 1
        filter_type_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        name_layout.addWidget(filter_type_combo)

        # Create filter table for this specific row
        filter_table = FolderFilterTable(self.GENRES, self.state.folder_configs)
        filters_data = filter_cfg.get("filters") or []
        for f in filters_data:
            filter_table.add_filter(f.get("filter", ""), f.get("value", ""))
        filter_table.cellChanged.connect(self._on_setting_changed)
        layout.addWidget(filter_table)

        container.name_edit = name_edit
        container.filter_table = filter_table

        add_btn = QPushButton("Add")
        add_btn.setIcon(APP_THEME.icon("fa5s.plus-circle", color=APP_THEME.text_color))
        add_btn.setIconSize(QSize(APP_THEME.icon_size - 5, APP_THEME.icon_size - 5))
        add_btn.setStyleSheet(APP_THEME.button_qss())
        add_btn.clicked.connect(
            lambda: self._add_filter_to_table(filter_table, filter_type_combo.currentText().strip())
        )

        delete_btn = QPushButton("")
        delete_btn.setIcon(APP_THEME.icon("fa5s.trash-alt", color=APP_THEME.text_color))
        delete_btn.setIconSize(QSize(APP_THEME.icon_size - 5, APP_THEME.icon_size - 5))
        delete_btn.setStyleSheet(APP_THEME.button_qss())
        delete_btn.clicked.connect(lambda: self._delete_filter(filter_cfg))

        name_layout.addWidget(add_btn)
        name_layout.addWidget(delete_btn)

        return container

    def _add_filter_to_table(self, filter_table: FolderFilterTable, filter_type: str) -> None:
        if filter_type.upper() in ("", "OS", "NFO"):
            return
        filter_table.add_filter(filter_type)
        self._on_setting_changed()

    def _update_state_from_ui(self) -> None:
        new_saved_filters = []
        for row in self.row_widgets:
            new_filter_cfg = {
                "name": row.name_edit.text(),
                "filters": row.filter_table.collect_filters()
            }
            new_saved_filters.append(new_filter_cfg)
        self.state.saved_filters = new_saved_filters

    def _delete_filter(self, filter_cfg: dict[str, Any]) -> None:
        self._update_state_from_ui()
        if filter_cfg in self.state.saved_filters:
            self.state.saved_filters.remove(filter_cfg)
        self._refresh_filters()
        self._on_setting_changed()

    def apply_theme(self) -> None:
        super().apply_theme()
        self._refresh_filters()

    def _save_filter_settings(self) -> None:
        """Save only Filters tab settings."""
        self._update_state_from_ui()
        self.state.save_filters()
        self.reset_save_button()
        self.sig_saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Filter Settings Saved",
                description="Filter settings were saved.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        print("Filters Settings saved")
