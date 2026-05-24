from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.settings.settings_app_tab import SettingsAppTab
from src.settings.settings_filter_tab import SettingsFilterTab
from src.settings.settings_media_tab import SettingsMediaTab
from src.settings.settings_state import SettingsState
from src.settings.settings_ui_tab import SettingsUITab
from src.theme.theme import APP_THEME
from src.widgets.right_aligned_tab_bar import RightAlignedTabBar


class Settings(QWidget):
    sig_dirty_changed = Signal(bool)

    def __init__(self, log_util) -> None:
        super().__init__()
        self.log_util = log_util
        self.log_util.debug(f"__init__ {self.__class__.__name__}")
        self.tab_widget = QTabWidget()
        self.help_icon = QLabel()
        self.state = SettingsState(self.log_util)
        self.ui_tab = SettingsUITab(self.state, self.log_util)
        self.media_tab = SettingsMediaTab(self.state, self.log_util)
        self.filter_tab = SettingsFilterTab(self.state, self.log_util)
        self.app_tab = SettingsAppTab(self.state, self.log_util)  # Add App tab

        # Connect signals
        self.state.sig_changed.connect(self.apply_theme)
        self.media_tab.sig_changed.connect(self.apply_theme)
        self.media_tab.sig_changed.connect(self.state.sig_changed.emit)

        # Wire dirty signals
        self.app_tab.sig_changed.connect(lambda: self._mark_dirty(self.app_tab))
        self.ui_tab.sig_changed.connect(lambda: self._mark_dirty(self.ui_tab))
        self.media_tab.sig_changed.connect(lambda: self._mark_dirty(self.media_tab))
        self.filter_tab.sig_changed.connect(lambda: self._mark_dirty(self.filter_tab))

        # Connect tab saved signals to check_all_saved
        self.app_tab.sig_saved.connect(self._check_all_saved)
        self.ui_tab.sig_saved.connect(self._check_all_saved)
        self.media_tab.sig_saved.connect(self._check_all_saved)
        self.filter_tab.sig_saved.connect(self._check_all_saved)

    @property
    def folder_configs(self):
        return self.state.folder_configs

    @folder_configs.setter
    def folder_configs(self, value):
        self.state.folder_configs = value

    @property
    def saved_filters(self):
        return self.state.saved_filters

    @saved_filters.setter
    def saved_filters(self, value):
        self.state.saved_filters = value

    @property
    def sig_changed(self):
        return self.state.sig_changed

    def build(self) -> QWidget:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        tab_bar = RightAlignedTabBar(self.tab_widget, spacer_index=0)
        self.tab_widget.setTabBar(tab_bar)
        self.tab_widget.setStyleSheet(APP_THEME.tabs_qss())
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # Spacer Tab (Index 0)
        spacer = QWidget()
        self.tab_widget.addTab(spacer, "")
        self.tab_widget.setTabEnabled(0, False)
        tab_bar.setTabButton(0, QTabBar.ButtonPosition.LeftSide, None)
        tab_bar.setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

        # Add Tabs
        self.tab_widget.addTab(self.app_tab, "  App  ")
        self.tab_widget.addTab(self.ui_tab, "   UI   ")
        self.tab_widget.addTab(self.media_tab, " Media ")
        self.tab_widget.addTab(self.filter_tab, " Filters ")

        # Select first real tab (index 1) as 0 is spacer
        if self.tab_widget.count() > 1:
            self.tab_widget.setCurrentIndex(1)

        main_layout.addWidget(self.tab_widget)

        return self

    def _mark_dirty(self, tab):
        tab.highlight_save_button()
        self.sig_dirty_changed.emit(True)

    def _check_all_saved(self):
        # If no tab is dirty, emit False
        # print(f"_check_all_saved: self.media_tab.is_dirty:{self.media_tab.is_dirty}")
        if not (self.app_tab.is_dirty or
                self.ui_tab.is_dirty or
                self.media_tab.is_dirty or
                self.filter_tab.is_dirty):
            self.sig_dirty_changed.emit(False)

    def _save_all_settings(self):
        """Save all tabs' settings."""
        self.state.save_settings()

        # Reset dirty state for all tabs
        self.app_tab.reset_save_button()
        self.ui_tab.reset_save_button()
        self.media_tab.reset_save_button()
        self.filter_tab.reset_save_button()

        self.show_save_status("All Settings saved")
        self._check_all_saved()

    def show_save_status(self, message: str):
        """Show a brief status notification."""
        msg = f"✔ {message}"
        print(msg)  # Log to console as status feedback

    def apply_theme(self):
        self.tab_widget.setStyleSheet(APP_THEME.tabs_qss())
        self.help_icon.setStyleSheet(
            APP_THEME.label_qss("small")
            + "; border: 1px solid palette(text); border-radius: 10px;"
        )
        self.ui_tab.apply_theme()
        self.media_tab.apply_theme()
        self.filter_tab.apply_theme()


    def save_filter(self, name: str, filters: list[dict]):
        self.state.save_filter(name, filters)

    def delete_filter(self, name: str):
        self.state.delete_filter(name)
