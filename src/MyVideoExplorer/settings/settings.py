from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTabBar, QTabWidget, QVBoxLayout, QWidget

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.settings.settings_app_tab import SettingsAppTab
from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.settings.settings_filter_tab import SettingsFilterTab
from MyVideoExplorer.settings.settings_media_tab import SettingsMediaTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.settings.settings_ui_tab import SettingsUITab
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.right_aligned_tab_bar import RightAlignedTabBar


class Settings(QWidget, ThemableMixin):
    """Container widget for application settings, managing tabs and state persistence."""

    dirty_changed = Signal(object)

    def __init__(self, log_util: LogUtil, file_util: FileUtil) -> None:
        super().__init__()
        self.log_util = log_util
        self.file_util = file_util

        # Data Model (State Management)
        self.settings_data_model = SettingsState(self.log_util)

        # View Components (Settings Tabs) - Initialized in _build_ui
        self.managed_tabs: list[SettingsBaseTab] = []
        self._app_settings_tab: SettingsAppTab | None = None
        self._ui_settings_tab: SettingsUITab | None = None
        self._media_settings_tab: SettingsMediaTab | None = None
        self._filter_settings_tab: SettingsFilterTab | None = None

    @property
    def app_settings_tab(self) -> SettingsAppTab:
        if self._app_settings_tab is None:
            self._build_ui()
            self._connect_signals()
        assert self._app_settings_tab is not None
        return self._app_settings_tab

    @property
    def ui_settings_tab(self) -> SettingsUITab:
        if self._ui_settings_tab is None:
            self._build_ui()
            self._connect_signals()
        assert self._ui_settings_tab is not None
        return self._ui_settings_tab

    @property
    def media_settings_tab(self) -> SettingsMediaTab:
        if self._media_settings_tab is None:
            self._build_ui()
            self._connect_signals()
        assert self._media_settings_tab is not None
        return self._media_settings_tab

    @property
    def filter_settings_tab(self) -> SettingsFilterTab:
        if self._filter_settings_tab is None:
            self._build_ui()
            self._connect_signals()
        assert self._filter_settings_tab is not None
        return self._filter_settings_tab

    def _build_ui(self) -> None:
        """Constructs the settings UI layout and registers tabs."""
        if self.layout() is not None:
            return

        # Initialize tabs if not already done
        if not self.managed_tabs:
            self._app_settings_tab = SettingsAppTab(
                self.settings_data_model, self.log_util, parent=self
            )
            self._ui_settings_tab = SettingsUITab(
                self.settings_data_model, self.log_util, self.file_util, parent=self
            )
            self._media_settings_tab = SettingsMediaTab(
                self.settings_data_model, self.log_util, self.file_util, parent=self
            )
            self._filter_settings_tab = SettingsFilterTab(
                self.settings_data_model, self.log_util, parent=self
            )

            # Group tabs for centralized management (DRY principle)
            self.managed_tabs = [
                self._app_settings_tab,
                self._ui_settings_tab,
                self._media_settings_tab,
                self._filter_settings_tab,
            ]

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.settings_tabs_container = QTabWidget(self)
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

        self.apply_theme()

    def _add_spacer_tab(self, tab_widget: QTabWidget, tab_bar: QTabBar) -> None:
        """Adds a disabled spacer tab to align other tabs to the right."""
        spacer = QWidget(self)
        spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        tab_widget.addTab(spacer, "")
        tab_widget.setTabEnabled(0, False)
        tab_bar.setTabButton(0, QTabBar.ButtonPosition.LeftSide, None)
        tab_bar.setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

    def _connect_signals(self) -> None:
        """Wires up signals between tabs, state, and the container."""
        self.settings_data_model.settings_changed.connect(lambda p: self.apply_theme())

        for tab in self.managed_tabs:
            # Use default argument to capture current loop variable correctly
            tab.changed.connect(lambda _, t=tab: self._mark_tab_dirty(t))
            tab.saved.connect(self._check_all_tabs_saved)

    def _mark_tab_dirty(self, tab: SettingsBaseTab) -> None:
        """Marks a specific tab as dirty and notifies the container."""
        tab.highlight_save_button()
        self.dirty_changed.emit(
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
            self.dirty_changed.emit(
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

        if self.layout() is None:
            return

        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.setFont(font)

        for tab in self.managed_tabs:
            tab.apply_theme()

        self.setStyleSheet(APP_THEME.app_qss())
        self.settings_tabs_container.setFont(font)

        # remove border around tab pane
        # qss pane border did not affect
        self.settings_tabs_container.setDocumentMode(True)

    def build(self) -> QWidget:
        """Ensures UI is constructed and returns the widget"""
        self._build_ui()
        return self

    # --- Data Model Delegation ---
    def get_media_configs(self):
        return self.settings_data_model.media_configs

    def set_media_configs(self, value):
        self.settings_data_model.media_configs = value

    def save_filter(self, name: str, filters: list[dict]) -> None:
        self.settings_data_model.save_filter(name, filters)

    def delete_filter(self, name: str) -> None:
        self.settings_data_model.delete_filter(name)
