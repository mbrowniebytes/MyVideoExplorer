from PySide6.QtCore import QSize, Qt, Signal
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

from src.theme.theme import APP_THEME


class SettingsFilterTab(QScrollArea):
    sig_changed = Signal()
    sig_saved = Signal()

    def __init__(self, state, log_util):
        super().__init__()
        self.log_util = log_util
        self.state = state
        self.is_dirty = False
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)

        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)

        self._build_ui()
        self.setWidget(self.main_widget)

    def _build_ui(self):
        self.filter_group = QGroupBox("Saved Filters")
        self.filter_layout = QVBoxLayout(self.filter_group)

        self._refresh_filters()

        self.layout.addWidget(self.filter_group)
        self.layout.addStretch(2)

        # Move Save Filters Settings button to bottom-right, centered
        save_btn_container = QWidget()
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.save_filter_btn = QPushButton("Save Filter Settings")
        self.save_filter_btn.setFixedWidth(180)
        self.save_filter_btn.setStyleSheet(APP_THEME.button_qss())
        self.save_filter_btn.clicked.connect(self._save_filter_settings)

        save_btn_layout.addWidget(self.save_filter_btn)
        self.layout.addWidget(
            save_btn_container,
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
        )

    def highlight_save_button(self):
        self.is_dirty = True
        self.save_filter_btn.setStyleSheet(APP_THEME.button_qss() + APP_THEME.button_highlight_qss())
        text_indicator = self.save_filter_btn.text().removesuffix(" *") + " *"
        self.save_filter_btn.setText(text_indicator)

    def reset_save_button(self):
        self.is_dirty = False
        self.save_filter_btn.setStyleSheet(APP_THEME.button_qss())
        text_indicator = self.save_filter_btn.text().removesuffix(" *")
        self.save_filter_btn.setText(text_indicator)

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
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        name_edit = QLineEdit(filter_cfg.get("name", ""))
        name_edit.setPlaceholderText("Filter Name")

        save_btn = QPushButton("Save")
        save_btn.setIcon(APP_THEME.icon("fa5s.save", color=APP_THEME.text_color))
        save_btn.setIconSize(QSize(APP_THEME.icon_size - 5, APP_THEME.icon_size - 5))
        save_btn.setStyleSheet(APP_THEME.button_qss())
        save_btn.clicked.connect(
            lambda: self._save_filter(filter_cfg, name_edit.text())
        )

        delete_btn = QPushButton("")
        delete_btn.setIcon(APP_THEME.icon("fa5s.trash-alt", color=APP_THEME.text_color))
        delete_btn.setIconSize(QSize(APP_THEME.icon_size - 5, APP_THEME.icon_size - 5))
        delete_btn.setStyleSheet(APP_THEME.button_qss())
        delete_btn.clicked.connect(lambda: self._delete_filter(filter_cfg))

        layout.addWidget(name_edit)
        layout.addWidget(save_btn)
        layout.addWidget(delete_btn)

        return container

    def _save_filter(self, filter_cfg: dict, new_name: str):
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
        self.state.sig_changed.emit()
        self.sig_changed.emit()
        self._refresh_filters()

    def _delete_filter(self, filter_cfg: dict):
        name = filter_cfg.get("name")
        self.state.delete_filter(name)
        self.sig_changed.emit()
        self._refresh_filters()

    def apply_theme(self):
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
