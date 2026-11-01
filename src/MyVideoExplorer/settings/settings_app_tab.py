from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
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
from MyVideoExplorer.settings.settings_state import (
    SCAN_MEDIA_TIMEOUT_OPTIONS,
    SettingsState,
)
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.combo_boxes.select_combo_box import SelectComboBox


class SettingsAppTab(SettingsBaseTab):
    def __init__(
        self, state: SettingsState, log_util: LogUtil, parent: QWidget | None = None
    ) -> None:
        super().__init__(log_util, parent)
        self.log_util = log_util
        self.state = state
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(15)

        self._build_ui()
        self._layout.addStretch()

    @property
    def internal_layout(self) -> QVBoxLayout:
        return self._layout

    def _build_ui(self) -> None:
        # App Settings group
        app_group = QGroupBox("App Settings")
        app_layout = QGridLayout()
        app_layout.setSpacing(5)

        row = 0
        # --- Group 1: On App Launch ---
        launch_label = QLabel("On App Launch")
        launch_label.setStyleSheet(APP_THEME.label_qss("group_row"))
        launch_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size + 1))
        app_layout.addWidget(launch_label, row, 0, 1, 1)

        # Separator line between groups
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedHeight(1)
        separator.setStyleSheet(
            f"background-color: {APP_THEME.border_color}; margin-left: 150px;"
        )
        app_layout.addWidget(separator, row, 0, 1, 2)
        row += 1

        # Auto select folder combo box
        self.app_start_select_prior_combo = SelectComboBox(self)
        self.app_start_select_prior_combo.addItem(
            "First Folder", "auto_select_first_folder"
        )
        self.app_start_select_prior_combo.addItem(
            "Prior Folder", "auto_select_prior_folder"
        )

        current_prior_select = getattr(
            self.state, "auto_select_folder", "auto_select_prior_folder"
        )
        index = self.app_start_select_prior_combo.findData(current_prior_select)
        if index >= 0:
            self.app_start_select_prior_combo.setCurrentIndex(index)

        auto_select_label = QLabel("Auto select folder")
        auto_select_label.setStyleSheet(APP_THEME.label_qss("nested"))
        app_layout.addWidget(auto_select_label, row, 0)
        app_layout.addWidget(self.app_start_select_prior_combo, row, 1)
        row += 1

        self.app_start_select_prior_combo.setToolTip(
            "When Folder Nav list refreshes, either select the First Folder, or the Prior Folder"
        )

        # App size combo box
        self.launch_app_size_combo = SelectComboBox(self)
        self.launch_app_size_combo.addItem("Last Window Size", "app_size_last")
        self.launch_app_size_combo.addItem("Maximized", "app_size_maximized")
        self.launch_app_size_combo.addItem("2560x1440", "app_size_2560x1440")
        self.launch_app_size_combo.addItem("1920x1080", "app_size_1920x1080")
        self.launch_app_size_combo.addItem("1600x960", "app_size_1600x960")
        self.launch_app_size_combo.addItem("1400x900", "app_size_1400x900")

        self.launch_app_size_combo.setToolTip(
            "Initial size of app window on launch; relative to DPI 100%"
        )

        current_launch_size = getattr(self.state, "launch_app_size", "app_size_min")
        if current_launch_size == "app_size_min":
            current_launch_size = "app_size_1200x800"
        index = self.launch_app_size_combo.findData(current_launch_size)
        if index >= 0:
            self.launch_app_size_combo.setCurrentIndex(index)

        self.launch_app_size_combo.currentIndexChanged.connect(
            self._on_launch_app_size_changed
        )
        self.launch_app_size_combo.currentIndexChanged.connect(self._on_setting_changed)

        app_size_label = QLabel("App size")
        app_size_label.setStyleSheet(APP_THEME.label_qss("nested"))
        app_layout.addWidget(app_size_label, row, 0)
        app_layout.addWidget(self.launch_app_size_combo, row, 1)
        row += 1

        # App position combo box
        self.launch_app_pos_combo = SelectComboBox(self)
        self.launch_app_pos_combo.addItem("Last Position", "app_pos_last")
        self.launch_app_pos_combo.addItem("Center Center", "app_pos_center_center")
        self.launch_app_pos_combo.addItem("Center Bottom", "app_pos_center_bottom")
        self.launch_app_pos_combo.addItem("Center Top", "app_pos_center_top")

        self.launch_app_pos_combo.setToolTip("Initial position of app window on launch")

        current_launch_pos = getattr(self.state, "launch_app_pos", "app_pos_last")
        index = self.launch_app_pos_combo.findData(current_launch_pos)
        if index >= 0:
            self.launch_app_pos_combo.setCurrentIndex(index)

        self.launch_app_pos_combo.currentIndexChanged.connect(
            self._on_launch_app_pos_changed
        )
        self.launch_app_pos_combo.currentIndexChanged.connect(self._on_setting_changed)

        app_pos_label = QLabel("App position")
        app_pos_label.setStyleSheet(APP_THEME.label_qss("nested"))
        app_layout.addWidget(app_pos_label, row, 0)
        app_layout.addWidget(self.launch_app_pos_combo, row, 1)
        row += 1

        # Loading screen combo box
        self.show_loading_screen_combo = SelectComboBox(self)
        self.show_loading_screen_combo.addItem("Hide", False)
        self.show_loading_screen_combo.addItem("Show", True)

        show_loading = getattr(self.state, "show_loading_screen", True)
        index = self.show_loading_screen_combo.findData(show_loading)
        if index >= 0:
            self.show_loading_screen_combo.setCurrentIndex(index)

        self.show_loading_screen_combo.currentIndexChanged.connect(
            self._on_loading_screen_changed
        )
        self.show_loading_screen_combo.currentIndexChanged.connect(
            self._on_setting_changed
        )
        loading_screen_label = QLabel("Loading screen")
        loading_screen_label.setStyleSheet(APP_THEME.label_qss("nested"))
        app_layout.addWidget(loading_screen_label, row, 0)
        app_layout.addWidget(self.show_loading_screen_combo, row, 1)
        row += 1

        # --- Group 2: Media ---
        media_label = QLabel("Media")
        media_label.setStyleSheet(APP_THEME.label_qss("group_row"))
        app_layout.addWidget(media_label, row, 0, 1, 1)

        # Separator line between groups
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedHeight(1)
        separator.setStyleSheet(
            f"background-color: {APP_THEME.border_color}; margin-left: 150px;"
        )
        app_layout.addWidget(separator, row, 0, 1, 2)
        row += 1

        # Scan media timeout combo box
        self.scan_media_timeout_combo = SelectComboBox(self)
        for timeout in SCAN_MEDIA_TIMEOUT_OPTIONS:
            self.scan_media_timeout_combo.addItem(f"{timeout}s", timeout)
        current_timeout = getattr(self.state, "scan_media_timeout_seconds", 120)
        index = self.scan_media_timeout_combo.findData(current_timeout)
        if index < 0:
            index = self.scan_media_timeout_combo.findData(120)
        self.scan_media_timeout_combo.setCurrentIndex(index)
        self.scan_media_timeout_combo.setToolTip(
            "Time without scan progress before a media scan is stopped."
        )
        self.scan_media_timeout_combo.currentIndexChanged.connect(
            self._on_scan_media_timeout_changed
        )
        self.scan_media_timeout_combo.currentIndexChanged.connect(
            self._on_setting_changed
        )
        scan_timeout_label = QLabel("Scan Media timeout")
        scan_timeout_label.setStyleSheet(APP_THEME.label_qss("nested"))
        app_layout.addWidget(scan_timeout_label, row, 0)
        app_layout.addWidget(self.scan_media_timeout_combo, row, 1)
        row += 1

        # NFO collapsed by default combo box
        self.nfo_collapsed_default_combo = SelectComboBox(self)
        self.nfo_collapsed_default_combo.addItem("Collapsed", True)
        self.nfo_collapsed_default_combo.addItem("Expanded", False)

        nfo_collapsed = getattr(self.state, "nfo_collapsed_by_default", False)
        index = self.nfo_collapsed_default_combo.findData(nfo_collapsed)
        if index >= 0:
            self.nfo_collapsed_default_combo.setCurrentIndex(index)

        self.nfo_collapsed_default_combo.setToolTip(
            "Whether the NFO column starts collapsed or expanded by default"
        )
        self.nfo_collapsed_default_combo.currentIndexChanged.connect(
            self._on_nfo_collapsed_default_changed
        )
        self.nfo_collapsed_default_combo.currentIndexChanged.connect(
            self._on_setting_changed
        )
        nfo_label = QLabel("NFO default state")
        nfo_label.setStyleSheet(APP_THEME.label_qss("nested"))
        app_layout.addWidget(nfo_label, row, 0)
        app_layout.addWidget(self.nfo_collapsed_default_combo, row, 1)
        row += 1

        # Meta collapsed by default combo box
        self.meta_collapsed_default_combo = SelectComboBox(self)
        self.meta_collapsed_default_combo.addItem("Collapsed", True)
        self.meta_collapsed_default_combo.addItem("Expanded", False)

        meta_collapsed = getattr(self.state, "meta_collapsed_by_default", False)
        index = self.meta_collapsed_default_combo.findData(meta_collapsed)
        if index >= 0:
            self.meta_collapsed_default_combo.setCurrentIndex(index)

        self.meta_collapsed_default_combo.setToolTip(
            "Whether the Meta column starts collapsed or expanded by default"
        )
        self.meta_collapsed_default_combo.currentIndexChanged.connect(
            self._on_meta_collapsed_default_changed
        )
        self.meta_collapsed_default_combo.currentIndexChanged.connect(
            self._on_setting_changed
        )
        meta_label = QLabel("Meta default state")
        meta_label.setStyleSheet(APP_THEME.label_qss("nested"))
        app_layout.addWidget(meta_label, row, 0)
        app_layout.addWidget(self.meta_collapsed_default_combo, row, 1)
        row += 1

        # --- Group 3: App ---
        app_label = QLabel("App")
        app_label.setStyleSheet(APP_THEME.label_qss("group_row"))
        app_layout.addWidget(app_label, row, 0, 1, 1)

        # Separator line between groups
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedHeight(1)
        separator.setStyleSheet(
            f"background-color: {APP_THEME.border_color}; margin-left: 150px;"
        )
        app_layout.addWidget(separator, row, 0, 1, 2)
        row += 1

        # Logging level combo box - populated from LogUtil.LEVEL_MAP
        self.logging_level_combo = SelectComboBox(self)
        for label in LogUtil.LEVEL_MAP:
            # Use capitalized display label matching the original format
            display_label = label.capitalize()
            self.logging_level_combo.addItem(display_label, label)

        # Set current value from state if available, default to info
        current_level = getattr(self.state, "log_level", "info")
        index = self.logging_level_combo.findData(current_level)
        if index >= 0:
            self.logging_level_combo.setCurrentIndex(index)

        self.logging_level_combo.setToolTip("Verbosity of App info logged to log/")
        logging_label = QLabel("Logging level")
        logging_label.setStyleSheet(APP_THEME.label_qss("nested"))
        app_layout.addWidget(logging_label, row, 0)
        app_layout.addWidget(self.logging_level_combo, row, 1)

        app_group.setLayout(app_layout)
        self.internal_layout.addWidget(app_group)

        # Add stretch to push save button to bottom
        self.internal_layout.addStretch(2)

        # Save App Settings button - bottom right, centered
        save_btn_container = QWidget(self)
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.save_btn = QPushButton("Save App Settings", parent=self)
        self.save_btn.setFixedWidth(200)
        self.save_btn.clicked.connect(self._save_app_settings)

        self.reset_btn = self._build_reset_button(
            "Reset App Settings", self.reset_settings
        )

        spacer = QWidget(self)
        spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        save_btn_layout.addWidget(self.reset_btn)
        save_btn_layout.addWidget(spacer)
        save_btn_layout.addWidget(self.save_btn)
        self.internal_layout.addWidget(
            save_btn_container,
            alignment=Qt.AlignmentFlag.AlignBottom,
        )

        self.logging_level_combo.currentIndexChanged.connect(self._on_setting_changed)
        self.app_start_select_prior_combo.currentIndexChanged.connect(
            self._on_setting_changed
        )
        self.launch_app_pos_combo.currentIndexChanged.connect(self._on_setting_changed)

    def apply_theme(self) -> None:
        super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.setFont(font)

    def _on_launch_app_size_changed(self, index: int) -> None:

        value = self.launch_app_size_combo.itemData(
            index, role=Qt.ItemDataRole.UserRole
        )
        if not value:
            return

        print(f"_on_launch_app_size_changed: index:{index} value:{value}")
        self.state.launch_app_size = value

        self.state.window_size_changed.emit(
            SignalPayload(
                data=value,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Launch app size was changed.",
                flow=SignalFlow.USER_INPUT,
            )
        )

    def _on_launch_app_pos_changed(self, index: int) -> None:

        value = self.launch_app_pos_combo.itemData(index, role=Qt.ItemDataRole.UserRole)
        if not value:
            return

        print(f"_on_launch_app_pos_changed: index:{index} value:{value}")

        self.state.window_pos_changed.emit(
            SignalPayload(
                data=value,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Launch app position was changed.",
                flow=SignalFlow.USER_INPUT,
            )
        )

    def _on_loading_screen_changed(self, index: int) -> None:
        value = self.show_loading_screen_combo.itemData(
            index, role=Qt.ItemDataRole.UserRole
        )
        self.state.show_loading_screen = value

        self.state.settings_changed.emit(
            SignalPayload(
                data=value,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Show loading screen setting was changed.",
                flow=SignalFlow.USER_INPUT,
            )
        )

    def _on_scan_media_timeout_changed(self, index: int) -> None:
        value = self.scan_media_timeout_combo.itemData(
            index, role=Qt.ItemDataRole.UserRole
        )
        if value not in SCAN_MEDIA_TIMEOUT_OPTIONS:
            return
        self.state.scan_media_timeout_seconds = value
        self.state.settings_changed.emit(
            SignalPayload(
                data=value,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Scan media timeout setting was changed.",
                flow=SignalFlow.USER_INPUT,
            )
        )

    def _on_nfo_collapsed_default_changed(self, index: int) -> None:
        value = self.nfo_collapsed_default_combo.itemData(
            index, role=Qt.ItemDataRole.UserRole
        )
        self.state.nfo_collapsed_by_default = value
        self.state.settings_changed.emit(
            SignalPayload(
                data=value,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="NFO default collapse setting was changed.",
                flow=SignalFlow.USER_INPUT,
            )
        )

    def _on_meta_collapsed_default_changed(self, index: int) -> None:
        value = self.meta_collapsed_default_combo.itemData(
            index, role=Qt.ItemDataRole.UserRole
        )
        self.state.meta_collapsed_by_default = value
        self.state.settings_changed.emit(
            SignalPayload(
                data=value,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Meta default collapse setting was changed.",
                flow=SignalFlow.USER_INPUT,
            )
        )

    def reset_settings(self) -> None:
        """Reset settings for this tab."""
        self.state.load_app()
        # Refresh combo box
        current_level = self.state.log_level
        index = self.logging_level_combo.findData(current_level)
        if index >= 0:
            self.logging_level_combo.setCurrentIndex(index)

        # Refresh prior folder combo box
        current_prior_select = getattr(
            self.state, "auto_select_folder", "auto_select_prior_folder"
        )
        index = self.app_start_select_prior_combo.findData(current_prior_select)
        if index >= 0:
            self.app_start_select_prior_combo.setCurrentIndex(index)

        # Update launch app size combo
        current_launch_size = getattr(self.state, "launch_app_size", "app_size_min")
        if current_launch_size == "app_size_min":
            current_launch_size = "app_size_1200x800"
        index = self.launch_app_size_combo.findData(current_launch_size)
        if index >= 0:
            self.launch_app_size_combo.setCurrentIndex(index)

        # Update launch app position combo
        current_launch_pos = getattr(self.state, "launch_app_pos", "app_pos_last")
        index = self.launch_app_pos_combo.findData(current_launch_pos)
        if index >= 0:
            self.launch_app_pos_combo.setCurrentIndex(index)

        # Update show loading screen combo
        current_show_loading = getattr(self.state, "show_loading_screen", True)
        index = self.show_loading_screen_combo.findData(current_show_loading)
        if index >= 0:
            self.show_loading_screen_combo.setCurrentIndex(index)

        index = self.scan_media_timeout_combo.findData(
            self.state.scan_media_timeout_seconds
        )
        if index >= 0:
            self.scan_media_timeout_combo.setCurrentIndex(index)

        # Update NFO collapsed default combo
        nfo_collapsed = getattr(self.state, "nfo_collapsed_by_default", False)
        index = self.nfo_collapsed_default_combo.findData(nfo_collapsed)
        if index >= 0:
            self.nfo_collapsed_default_combo.setCurrentIndex(index)

        # Update Meta collapsed default combo
        meta_collapsed = getattr(self.state, "meta_collapsed_by_default", False)
        index = self.meta_collapsed_default_combo.findData(meta_collapsed)
        if index >= 0:
            self.meta_collapsed_default_combo.setCurrentIndex(index)

        self.reset_save_button()
        self.saved.emit(
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
        # Save Show Loading Screen setting
        current_index = self.show_loading_screen_combo.currentIndex()
        if current_index >= 0:
            self.state.show_loading_screen = self.show_loading_screen_combo.itemData(
                current_index
            )

        current_index = self.scan_media_timeout_combo.currentIndex()
        if current_index >= 0:
            self.state.scan_media_timeout_seconds = (
                self.scan_media_timeout_combo.itemData(current_index)
            )

        # Get current logging level
        current_index = self.logging_level_combo.currentIndex()
        if current_index >= 0:
            log_level = self.logging_level_combo.itemData(current_index)
            self.state.log_level = log_level

        # Save prior folder selection setting
        current_index = self.app_start_select_prior_combo.currentIndex()
        if current_index >= 0:
            self.state.auto_select_folder = self.app_start_select_prior_combo.itemData(
                current_index
            )

        current_index = self.launch_app_size_combo.currentIndex()
        if current_index >= 0:
            self.state.launch_app_size = self.launch_app_size_combo.itemData(
                current_index
            )

        current_index = self.launch_app_pos_combo.currentIndex()
        if current_index >= 0:
            self.state.launch_app_pos = self.launch_app_pos_combo.itemData(
                current_index
            )

        # Save NFO collapsed default setting
        current_index = self.nfo_collapsed_default_combo.currentIndex()
        if current_index >= 0:
            self.state.nfo_collapsed_by_default = (
                self.nfo_collapsed_default_combo.itemData(current_index)
            )

        # Save Meta collapsed default setting
        current_index = self.meta_collapsed_default_combo.currentIndex()
        if current_index >= 0:
            self.state.meta_collapsed_by_default = (
                self.meta_collapsed_default_combo.itemData(current_index)
            )

        self.state.save_app()
        self.reset_save_button()
        self.saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="App Settings Saved",
                description="App settings were saved.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        # print("App Settings saved")
