from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
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

from src.theme.theme import APP_THEME


class SettingsUITab(QScrollArea):
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
        self.layout.addStretch()
        self.setWidget(self.main_widget)

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

        self.layout.addWidget(display_group)

        # Add stretch to push save button to bottom even when content is short
        self.layout.addStretch(2)

        # Move Save UI Settings button to bottom-right, centered
        save_btn_container = QWidget()
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.save_ui_btn = QPushButton("Save UI Settings")
        # self.save_ui_btn.setFixedWidth(180)
        self.save_ui_btn.setStyleSheet(APP_THEME.button_qss())
        self.save_ui_btn.clicked.connect(self._save_ui_settings)

        save_btn_layout.addWidget(self.save_ui_btn)
        self.layout.addWidget(
            save_btn_container,
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
        )

        self.font_size_spinbox.valueChanged.connect(self._on_setting_changed)

    def _on_setting_changed(self, value):
        self.sig_changed.emit()

    def highlight_save_button(self):
        self.is_dirty = True
        self.save_ui_btn.setStyleSheet(APP_THEME.button_qss() + APP_THEME.button_highlight_qss())
        text_indicator = self.save_ui_btn.text().removesuffix(" *") + " *"
        self.save_ui_btn.setText(text_indicator)

    def reset_save_button(self):
        self.is_dirty = False
        self.save_ui_btn.setStyleSheet(APP_THEME.button_qss())
        text_indicator = self.save_ui_btn.text().removesuffix(" *")
        self.save_ui_btn.setText(text_indicator)

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
        self.state.sig_changed.emit()

    def _save_ui_settings(self):
        """Save only UI tab settings."""
        self.state.save_ui()
        self.reset_save_button()
        self.sig_saved.emit()
        print("UI Settings saved")

    def apply_theme(self):
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.main_widget.setFont(font)
        self.main_widget.setStyleSheet(APP_THEME.container_qss())

        self.font_size_spinbox.setFont(font)
        self.font_size_spinbox.setValue(APP_THEME.font_size)
