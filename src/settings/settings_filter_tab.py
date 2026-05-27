from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.folder_filter.folder_filter_table import FolderFilterTable

from src.settings.settings_base_tab import SettingsBaseTab
from src.settings.settings_state import SettingsState
from src.theme.theme import APP_THEME
from src.utils.log_util import LogUtil


class SettingsFilterTab(SettingsBaseTab):
    # TODO centralize w/ folder_filter
    GENRES = sorted(
        ["Action", "Comedy", "Sci-Fi", "Mystery", "Thriller", "Drama", "Adventure"]
    )

    def __init__(self, state: SettingsState, log_util: LogUtil, parent=None):
        super().__init__(log_util, parent)
        self.state = state

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

        self.filter_table = FolderFilterTable(self.GENRES, self.state.folder_configs)

        self._build_ui()
        self.content_layout.addStretch()

        scroll.setWidget(self.main_widget)
        self.layout.addWidget(scroll)

    def _build_ui(self):
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
        self.save_btn.setStyleSheet(APP_THEME.button_qss())
        self.save_btn.clicked.connect(self._save_filter_settings)

        save_btn_layout.addWidget(self.save_btn)
        self.content_layout.addWidget(
            save_btn_container,
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
        )

    def highlight_save_button(self):
        self.is_dirty = True
        self.save_btn.setStyleSheet(APP_THEME.button_qss() + APP_THEME.button_highlight_qss())
        text_indicator = self.save_btn.text().removesuffix(" *") + " *"
        self.save_btn.setText(text_indicator)

    def reset_save_button(self):
        self.is_dirty = False
        self.save_btn.setStyleSheet(APP_THEME.button_qss())
        text_indicator = self.save_btn.text().removesuffix(" *")
        self.save_btn.setText(text_indicator)

    def _refresh_filters(self):
        # Clear existing filter rows
        while self.filter_layout.count():
            child = self.filter_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.state.saved_filters:
            self.filter_layout.addWidget(QLabel("No saved filters found."))
            return

        for filter_cfg in self.state.saved_filters:
            row_widget = self._make_filter_row(filter_cfg)
            self.filter_layout.addWidget(row_widget)

    def _make_filter_row(self, filter_cfg: dict) -> QWidget:
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
        name_layout.addWidget(name_edit)

        add_btn = QPushButton("Add")
        add_btn.setIcon(APP_THEME.icon("fa5s.plus-circle", color=APP_THEME.text_color))
        add_btn.setIconSize(QSize(APP_THEME.icon_size - 5, APP_THEME.icon_size - 5))
        add_btn.setStyleSheet(APP_THEME.button_qss())
        # add_btn.clicked.connect(
        #     lambda: self.filter_table.add_filter()
        # )

        delete_btn = QPushButton("")
        delete_btn.setIcon(APP_THEME.icon("fa5s.trash-alt", color=APP_THEME.text_color))
        delete_btn.setIconSize(QSize(APP_THEME.icon_size - 5, APP_THEME.icon_size - 5))
        delete_btn.setStyleSheet(APP_THEME.button_qss())
        delete_btn.clicked.connect(lambda: self._delete_filter(filter_cfg))

        name_layout.addWidget(add_btn)
        name_layout.addWidget(delete_btn)

        filters_data = filter_cfg.get("filters") or []
        for f in filters_data:
            self.filter_table.add_filter(f.get("filter", ""), f.get("value", ""))
        layout.addWidget(self.filter_table)

        return container

    def _add_filter(self, filter_cfg: dict, new_name: str):
        if not new_name.strip():
            return

        # Update name in the config
        old_name = filter_cfg.get("name")
        if old_name == new_name:
            # Nothing changed in name, but maybe we want to save anyway?
            # The issue asks to allow renaming.
            pass

        filter_cfg["name"] = new_name
        self.state.save_filters()
        # self.state.sig_changed.emit()
        self.sig_changed.emit()
        self._refresh_filters()

    def _delete_filter(self, filter_cfg: dict):
        name = filter_cfg.get("name")
        # self.state.delete_filter(name)
        # self.sig_changed.emit()
        # self._refresh_filters()

    def apply_theme(self):
        super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.main_widget.setFont(font)
        self.main_widget.setStyleSheet(APP_THEME.container_qss())
        self._refresh_filters()

    def _save_filter_settings(self):
        """Save only Filters tab settings."""
        self.state.save_filters()
        self.reset_save_button()
        self.sig_saved.emit()
        print("Filters Settings saved")
