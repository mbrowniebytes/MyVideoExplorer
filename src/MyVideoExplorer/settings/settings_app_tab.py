from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil


class SettingsAppTab(SettingsBaseTab):
    def __init__(
        self, state: SettingsState, log_util: LogUtil, parent: QWidget | None = None
    ) -> None:
        super().__init__(log_util, parent)
        self.log_util = log_util
        self.state = state
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)

        self._build_ui()
        self.layout.addStretch()

    def _build_ui(self) -> None:
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

        # App start prior folder selection combo box
        self.app_start_select_prior_combo = QComboBox()
        self.app_start_select_prior_combo.addItem("First Folder", "auto_select_first_folder")
        self.app_start_select_prior_combo.addItem("Prior Folder", "auto_select_prior_folder")

        current_prior_select = getattr(self.state, "auto_select_folder", "auto_select_prior_folder")
        index = self.app_start_select_prior_combo.findData(current_prior_select)
        if index >= 0:
            self.app_start_select_prior_combo.setCurrentIndex(index)

        app_layout.addRow("Auto Select Folder", self.app_start_select_prior_combo)

        self.app_start_select_prior_combo.setToolTip("When Folder Nav list refreshes, either select the First Folder, or the Prior Folder")

        self.logging_level_combo.setToolTip("Verbosity of App info logged to log/")
        app_layout.addRow("Logging Level", self.logging_level_combo)

        self.layout.addWidget(app_group)

        # Add stretch to push save button to bottom
        self.layout.addStretch(2)

        # Save App Settings button - bottom right, centered
        save_btn_container = QWidget()
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.save_btn = QPushButton("Save App Settings")
        self.save_btn.setFixedWidth(180)
        self.save_btn.clicked.connect(self._save_app_settings)

        self.reset_btn = self._build_reset_button(
            "Reset App Settings", self.reset_settings
        )

        spacer = QWidget()
        spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        save_btn_layout.addWidget(self.reset_btn)
        save_btn_layout.addWidget(spacer)
        save_btn_layout.addWidget(self.save_btn)
        self.layout.addWidget(
            save_btn_container,
            alignment=Qt.AlignmentFlag.AlignBottom,
        )

        self.logging_level_combo.currentIndexChanged.connect(self._on_setting_changed)
        self.app_start_select_prior_combo.currentIndexChanged.connect(
            self._on_setting_changed
        )

    def apply_theme(self) -> None:
        super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.setFont(font)

    def reset_settings(self) -> None:
        """Reset settings for this tab."""
        self.state.load_app()
        # Refresh combo box
        current_level = self.state.log_level
        index = self.logging_level_combo.findData(current_level)
        if index >= 0:
            self.logging_level_combo.setCurrentIndex(index)

        # Refresh prior folder combo box
        current_prior_select = getattr(self.state, "auto_select_folder", "auto_select_prior_folder")
        index = self.app_start_select_prior_combo.findData(current_prior_select)
        if index >= 0:
            self.app_start_select_prior_combo.setCurrentIndex(index)

        self.reset_save_button()
        self.sig_saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="App Settings Reset",
                description="App settings were reset to defaults.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        print("App Settings reset")

    def _save_app_settings(self) -> None:
        """Save only App tab settings."""
        # Get current logging level
        current_index = self.logging_level_combo.currentIndex()
        if current_index >= 0:
            log_level = self.logging_level_combo.itemData(current_index)
            self.state.log_level = log_level

        # Save prior folder selection setting
        current_index = self.app_start_select_prior_combo.currentIndex()
        if current_index >= 0:
            self.state.auto_select_prior_folder = (
                self.app_start_select_prior_combo.itemData(current_index)
            )

        self.state.save_app()
        self.reset_save_button()
        self.sig_saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="App Settings Saved",
                description="App settings were saved.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        # print("App Settings saved")
