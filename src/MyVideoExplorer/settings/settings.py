from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTabBar, QTabWidget, QVBoxLayout, QWidget

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.settings.settings_app_tab import SettingsAppTab
from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.settings.settings_filter_tab import SettingsFilterTab
from MyVideoExplorer.settings.settings_media_tab import SettingsMediaTab
from MyVideoExplorer.settings.settings_state import SettingsState

# from MyVideoExplorer.settings.settings_ui_tab import SettingsUITab
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.base_widget import BaseWidget
from MyVideoExplorer.widgets.right_aligned_tab_bar import RightAlignedTabBar


class Settings(BaseWidget):
    """Container widget for application settings, managing tabs and state persistence."""

    sig_dirty_changed = Signal(object)

    def __init__(self, log_util: LogUtil) -> None:
        super().__init__(log_util)
        self.log_util = log_util

        # Data Model (State Management)
        self.settings_data_model = SettingsState(self.log_util)

        # View Components (Settings Tabs)
        from MyVideoExplorer.settings.settings_ui_tab import SettingsUITab

        self.app_settings_tab = SettingsAppTab(self.settings_data_model, self.log_util)
        self.ui_settings_tab = SettingsUITab(self.settings_data_model, self.log_util)
        self.media_settings_tab = SettingsMediaTab(
            self.settings_data_model, self.log_util
        )
        self.filter_settings_tab = SettingsFilterTab(
            self.settings_data_model, self.log_util
        )

        # Group tabs for centralized management (DRY principle)
        self.managed_tabs: list[SettingsBaseTab] = [
            self.app_settings_tab,
            self.ui_settings_tab,
            self.media_settings_tab,
            self.filter_settings_tab,
        ]

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        """Constructs the settings UI layout and registers tabs."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.settings_tabs_container = QTabWidget()
        tab_bar = RightAlignedTabBar(self.settings_tabs_container, spacer_index=0)
        self.settings_tabs_container.setTabBar(tab_bar)
        self.settings_tabs_container.setTabPosition(QTabWidget.TabPosition.North)

        # Add invisible spacer tab to push functional tabs right
        self._add_spacer_tab(self.settings_tabs_container, tab_bar)

        # Register settings tabs with consistent labels
        tab_labels = ["App", "UI", "Media", "Filters"]
        for tab_widget, label in zip(self.managed_tabs, tab_labels):
            self.settings_tabs_container.addTab(tab_widget, f" {label} ")

        # Default to first functional tab (index 1)
        if self.settings_tabs_container.count() > 1:
            self.settings_tabs_container.setCurrentIndex(1)

        main_layout.addWidget(self.settings_tabs_container)

    @staticmethod
    def _add_spacer_tab(tab_widget: QTabWidget, tab_bar: QTabBar) -> None:
        """Adds a disabled spacer tab to align other tabs to the right."""
        spacer = QWidget()
        spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        tab_widget.addTab(spacer, "")
        tab_widget.setTabEnabled(0, False)
        tab_bar.setTabButton(0, QTabBar.ButtonPosition.LeftSide, None)
        tab_bar.setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

    def _connect_signals(self) -> None:
        """Wires up signals between tabs, state, and the container."""
        self.settings_data_model.sig_settings_changed.connect(
            lambda p: self.apply_theme()
        )

        for tab in self.managed_tabs:
            # Use default argument to capture current loop variable correctly
            tab.sig_changed.connect(lambda _, t=tab: self._mark_tab_dirty(t))
            tab.sig_saved.connect(self._check_all_tabs_saved)

    def _mark_tab_dirty(self, tab: SettingsBaseTab) -> None:
        """Marks a specific tab as dirty and notifies the container."""
        tab.highlight_save_button()
        self.sig_dirty_changed.emit(
            SignalPayload(
                data=True,
                sender=self.__class__.__name__,
                name="Dirty Changed",
                description="Settings tab state changed to dirty.",
                flow=SignalFlow.COMPONENT_INTERACTION,
            )
        )

    def _check_all_tabs_saved(self) -> None:
        """Checks if all tabs are clean. Emits False if no dirty tabs remain."""
        is_dirty = False
        for t in self.managed_tabs:
            if t.is_dirty:
                is_dirty = True
                break

        if not is_dirty:
            self.sig_dirty_changed.emit(
                SignalPayload(
                    data=False,
                    sender=self.__class__.__name__,
                    name="Dirty Changed",
                    description="Settings tab state changed to clean.",
                    flow=SignalFlow.COMPONENT_INTERACTION,
                )
            )

    def save_all_settings(self) -> None:
        """Persists settings from all tabs and resets dirty states."""
        self.settings_data_model.save_settings()

        for tab in self.managed_tabs:
            if hasattr(tab, "reset_save_button"):
                tab.reset_save_button()

        self.log_util.info("All Settings saved")
        self._check_all_tabs_saved()

    def apply_theme(self) -> None:
        """Applies current theme to the settings container and all managed tabs."""
        super().apply_theme()
        # self.settings_tabs_container.setStyleSheet(APP_THEME.tabs_qss()) # Handled by ThemeManager

        for tab in self.managed_tabs:
            if hasattr(tab, "apply_theme"):
                tab.apply_theme()

    def build(self) -> QWidget:
        """Ensures UI is constructed and returns the widget (backward compatibility)."""
        if not hasattr(self, "settings_tabs_container"):
            self._build_ui()
        return self

    # --- Data Model Delegation ---
    def get_folder_configs(self):
        return self.settings_data_model.folder_configs

    def set_folder_configs(self, value):
        self.settings_data_model.folder_configs = value

    def save_filter(self, name: str, filters: list[dict]) -> None:
        self.settings_data_model.save_filter(name, filters)

    def delete_filter(self, name: str) -> None:
        self.settings_data_model.delete_filter(name)
