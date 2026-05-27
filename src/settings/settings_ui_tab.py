from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from src.settings.settings_base_tab import SettingsBaseTab
from src.settings.settings_state import SettingsState
from src.theme.theme import APP_THEME
from src.utils.log_util import LogUtil


class SettingsUITab(SettingsBaseTab):
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
        
        self._build_ui()
        self.content_layout.addStretch()
        
        scroll.setWidget(self.main_widget)
        self.layout.addWidget(scroll)

    def _build_ui(self):
        display_group = QGroupBox("UI Settings")
        display_layout = QFormLayout(display_group)

        # Font size
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setMinimum(10)
        self.font_size_spinbox.setMaximum(24)
        self.font_size_spinbox.setValue(APP_THEME.font_size)
        self.font_size_spinbox.valueChanged.connect(self._on_font_size_changed)
        display_layout.addRow("Font Size:", self.font_size_spinbox)

        self.content_layout.addWidget(display_group)

        # Add stretch to push save button to bottom even when content is short
        self.content_layout.addStretch(2)

        # Move Save UI Settings button to bottom-right, centered
        save_btn_container = QWidget()
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.save_btn = QPushButton("Save UI Settings")
        self.save_btn.setStyleSheet(APP_THEME.button_qss())
        self.save_btn.clicked.connect(self._save_ui_settings)

        save_btn_layout.addWidget(self.save_btn)
        self.content_layout.addWidget(
            save_btn_container,
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
        )

        self.font_size_spinbox.valueChanged.connect(lambda: self._on_setting_changed())

    def _on_font_size_changed(self, value: int):
        if value == APP_THEME.font_size:
            return

        APP_THEME.font_size = value
        # Block signals on spinbox before refresh_theme to prevent re-triggering during apply_theme
        self.font_size_spinbox.blockSignals(True)
        try:
            APP_THEME.refresh_theme()
        finally:
            self.font_size_spinbox.blockSignals(False)
        self.state.sig_settings_changed.emit()

    def _save_ui_settings(self):
        """Save only UI tab settings."""
        self.state.save_ui()
        self.reset_save_button()
        self.sig_saved.emit()
        print("UI Settings saved")

    def apply_theme(self):
        super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.main_widget.setFont(font)
        self.main_widget.setStyleSheet(APP_THEME.container_qss())

        self.font_size_spinbox.setFont(font)
        self.font_size_spinbox.setValue(APP_THEME.font_size)
