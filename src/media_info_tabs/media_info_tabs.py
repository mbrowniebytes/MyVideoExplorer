from PySide6.QtCore import Signal
from PySide6.QtGui import QFont, Qt
from PySide6.QtWidgets import QTabBar, QTabWidget, QVBoxLayout, QWidget

from src.image_list.image_list import ImageList
from src.media_info.media_info import MediaInfo
from src.settings.settings import Settings
from src.theme.theme import APP_THEME
from src.widgets.base_widget import BaseWidget
from src.widgets.right_aligned_tab_bar import RightAlignedTabBar


class MediaInfoTabs(BaseWidget):
    """Widget container managing the tabbed interface for media, metadata, and settings."""

    sig_tab_selection_changed = Signal(int)

    LABEL_MEDIA = "media"
    LABEL_INFO = "info"
    LABEL_SETTINGS = "⚙"
    LABEL_SETTINGS_DIRTY = "⚙*"

    def __init__(self, log_util) -> None:
        super().__init__(log_util)
        self.folder_path: str | None = None
        self.active_tab_index: int = 0
        self.spacer_tab_index: int = -1
        self.settings_tab_index: int = -1
        self._signals_connected: bool = False

        # Components
        self.tab_container = QTabWidget()
        self.tab_container.setTabBar(RightAlignedTabBar(self.tab_container))

        self.image_list: ImageList | None = None
        self.media_info: MediaInfo | None = None

        # Layout setup for MediaInfoTabs itself
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tab_container)

    def build(
        self,
        media_info: MediaInfo,
        image_list: ImageList,
        settings: Settings,
    ) -> QTabWidget:
        """Initializes the tab structure and returns the underlying tab widget."""
        self.media_info = media_info
        self.image_list = image_list

        self._initialize_tabs(settings)
        self._connect_signals()

        self.tab_container.setStyleSheet(APP_THEME.tabs_qss())
        return self.tab_container

    def _initialize_tabs(self, settings: Settings) -> None:
        if self.tab_container.count() != 0:
            return

        self.tab_container.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_container.setFont(self._get_theme_font())

        # Add content tabs
        self._add_content_tab(self.image_list.build(), self.LABEL_MEDIA)
        self._add_content_tab(self.media_info.build(), self.LABEL_INFO)
        self._add_spacer_tab()
        self._add_settings_tab(settings)

    def _add_content_tab(self, widget: QWidget, label: str) -> int:
        """Wraps a widget in a layout-managed container and adds it as a tab."""
        tab_page = QWidget()
        layout = QVBoxLayout(tab_page)
        layout.addWidget(widget)
        return self.tab_container.addTab(tab_page, label)

    def _add_spacer_tab(self) -> None:
        """Adds a non-functional spacer tab to push following tabs to the right."""
        spacer = QWidget()
        spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.spacer_tab_index = self.tab_container.addTab(spacer, "")
        self.tab_container.setTabEnabled(self.spacer_tab_index, False)

        # Ensure buttons are removed from the tab bar for this index
        bar = self.tab_container.tabBar()
        bar.setTabButton(self.spacer_tab_index, QTabBar.ButtonPosition.LeftSide, None)
        bar.setTabButton(self.spacer_tab_index, QTabBar.ButtonPosition.RightSide, None)

    def _add_settings_tab(self, settings: Settings) -> None:
        self.settings_tab_index = self._add_content_tab(settings.build(), self.LABEL_SETTINGS)
        settings.sig_dirty_changed.connect(lambda p: self._on_settings_dirty_changed(p.data))

    def _on_settings_dirty_changed(self, is_dirty: bool) -> None:
        label = self.LABEL_SETTINGS_DIRTY if is_dirty else self.LABEL_SETTINGS
        self.tab_container.setTabText(self.settings_tab_index, label)

    def show_settings_tab(self) -> None:
        if self.settings_tab_index != -1:
            self.tab_container.setCurrentIndex(self.settings_tab_index)

    def _connect_signals(self) -> None:
        if self._signals_connected:
            return
        self.tab_container.currentChanged.connect(self._on_tab_index_changed)
        self._signals_connected = True

    def _on_tab_index_changed(self, index: int) -> None:
        if index == self.active_tab_index or index == self.spacer_tab_index:
            return

        self.active_tab_index = index
        self.sig_tab_selection_changed.emit(index)
        self.log_util.debug(f"Tab selection changed to index: {index}")

    def _get_theme_font(self) -> QFont:
        return QFont(APP_THEME.font_family, APP_THEME.font_size)

    def set_folder_path(self, folder_path: str) -> None:
        self.folder_path = folder_path

    def apply_theme(self) -> None:
        font = self._get_theme_font()
        self.setFont(font)
        self.tab_container.setFont(font)
        self.tab_container.setStyleSheet(APP_THEME.tabs_qss())

        if self.media_info:
            self.media_info.apply_theme()

        for i in range(self.tab_container.count()):
            widget = self.tab_container.widget(i)
            if widget:
                widget.setFont(font)
