from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.settings.settings_base_tab import SettingsBaseTab
from src.theme.theme import APP_THEME
from src.utils.log_util import LogUtil


class SettingsAppTab(SettingsBaseTab):
    def __init__(self, state, log_util, parent=None):
        super().__init__(log_util, parent)
        self.log_util = log_util
        self.state = state
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)

        self._build_ui()
        self.layout.addStretch()

    def _build_ui(self):
        # App Settings group
        app_group = QGroupBox("App Settings")
        app_layout = QFormLayout(app_group)

        # Logging level combo box - populated from LogUtil.LEVEL_MAP
        self.logging_level_combo = QComboBox()
        for label, value in LogUtil.LEVEL_MAP.items():
            # Use capitalized display label matching the original format
            display_label = label.capitalize()
            self.logging_level_combo.addItem(display_label, label)

        # Set current value from state if available, default to info
        current_level = getattr(self.state, "log_level", "info")
        index = self.logging_level_combo.findData(current_level)
        if index >= 0:
            self.logging_level_combo.setCurrentIndex(index)

        app_layout.addRow("Logging Level:", self.logging_level_combo)

        self.layout.addWidget(app_group)

        # Add stretch to push save button to bottom
        self.layout.addStretch(2)

        # Save App Settings button - bottom right, centered
        save_btn_container = QWidget()
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.save_btn = QPushButton("Save App Settings")
        self.save_btn.setFixedWidth(180)
        self.save_btn.setStyleSheet(APP_THEME.button_qss())
        self.save_btn.clicked.connect(self._save_app_settings)

        save_btn_layout.addWidget(self.save_btn)
        self.layout.addWidget(
            save_btn_container,
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
        )

        self.logging_level_combo.currentIndexChanged.connect(self._on_setting_changed)

    def _save_app_settings(self):
        """Save only App tab settings."""
        # Get current logging level
        current_index = self.logging_level_combo.currentIndex()
        if current_index >= 0:
            log_level = self.logging_level_combo.itemData(current_index)
            self.state.log_level = log_level

        self.state.save_app()
        self.reset_save_button()
        self.sig_saved.emit()
        print("App Settings saved")
