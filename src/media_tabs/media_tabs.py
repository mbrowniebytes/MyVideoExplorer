from PySide6.QtCore import Signal
from PySide6.QtGui import QFont, Qt
from PySide6.QtWidgets import QTabBar, QTabWidget, QVBoxLayout, QWidget

from src.image_list.image_list import ImageList
from src.media_info.media_info import MediaInfo
from src.settings.settings import Settings
from src.theme.theme import APP_THEME
from src.widgets.base_widget import BaseWidget
from src.widgets.right_aligned_tab_bar import RightAlignedTabBar


class MediaTabs(BaseWidget):
    sig_tab_click = Signal(int)

    def __init__(self, log_util) -> None:
        super().__init__(log_util)
        self.folder_path = None
        self.media_info_tabs = QTabWidget()
        tab_bar = RightAlignedTabBar(self.media_info_tabs)
        self.media_info_tabs.setTabBar(tab_bar)
        self.image_list: ImageList | None = None
        self.media_info: MediaInfo | None = None
        self.current_tab = 0
        self._signals_connected = False

    def build(
        self,
        media_info: MediaInfo,
        image_list: ImageList,
        settings: Settings,
    ):
        self.image_list = image_list
        self.media_info = media_info
        self._build_tabs(media_info, image_list, settings)
        self._connect_sigs()
        self.media_info_tabs.setStyleSheet(APP_THEME.tabs_qss())
        return self.media_info_tabs

    def _build_tabs(
        self,
        media_info: MediaInfo,
        image_list: ImageList,
        settings: Settings,
    ) -> None:
        if self.media_info_tabs.count() != 0:
            return

        self._configure_tabs()
        self._add_media_tab(image_list)
        self._add_info_tab(media_info)
        self._add_spacer_tab()
        self._add_settings_tab(settings)

    def _add_spacer_tab(self) -> None:
        spacer = QWidget()
        spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.media_info_tabs.addTab(spacer, "")
        idx = self.media_info_tabs.count() - 1
        self.media_info_tabs.setTabEnabled(idx, False)
        # Ensure it doesn't show up in any list of tabs or can be styled away
        tab_bar = self.media_info_tabs.tabBar()
        tab_bar.setTabButton(idx, QTabBar.ButtonPosition.LeftSide, None)
        tab_bar.setTabButton(idx, QTabBar.ButtonPosition.RightSide, None)

    def _configure_tabs(self) -> None:
        self.media_info_tabs.setTabPosition(QTabWidget.TabPosition.North)
        # self.media_info_tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.media_info_tabs.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))

    def _add_media_tab(self, image_list: ImageList) -> None:
        media_tab = QWidget()
        media_tab_layout = QVBoxLayout(media_tab)
        media_tab_layout.addWidget(image_list.build())
        self.media_info_tabs.addTab(media_tab, "media")

    def _add_info_tab(self, media_info: MediaInfo) -> None:
        info_tab = QWidget()
        info_tab_layout = QVBoxLayout(info_tab)
        info_tab_layout.addWidget(media_info.build())
        self.media_info_tabs.addTab(info_tab, "info")

    def _add_settings_tab(self, settings: Settings) -> None:
        settings_tab = QWidget()
        settings_tab_layout = QVBoxLayout(settings_tab)
        settings_tab_layout.addWidget(settings.build())
        self.media_info_tabs.addTab(settings_tab, "⚙")
        settings.sig_dirty_changed.connect(self._update_gear_tab_highlight)

    def _update_gear_tab_highlight(self, is_dirty: bool) -> None:
        index = self.media_info_tabs.count() - 1
        if is_dirty:
            self.media_info_tabs.tabBar().setTabText(index, "⚙*")
        else:
            self.media_info_tabs.tabBar().setTabText(index, "⚙")

    def show_settings_tab(self) -> None:
        # Assuming settings is the last tab added
        self.media_info_tabs.setCurrentIndex(self.media_info_tabs.count() - 1)

    def _connect_sigs(self) -> None:
        if self._signals_connected:
            return
        self.media_info_tabs.currentChanged.connect(self._on_tab_clicked)
        self._signals_connected = True

    def _on_tab_clicked(self, index: int) -> None:
        if self.current_tab == index:
            return
        if index == self.media_info_tabs.count() - 2:  # Spacer tab
            return
        self.current_tab = index
        self.sig_tab_click.emit(index)
        self.log_util.debug(f"sig_tab_click emitted with: {index}")

    def set_folder_path(self, folder_path: str) -> None:
        self.folder_path = folder_path

    def apply_theme(self) -> None:
        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.media_info_tabs.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.media_info_tabs.setStyleSheet(APP_THEME.tabs_qss())

        if self.media_info is not None:
            self.media_info.apply_theme()

        for index in range(self.media_info_tabs.count()):
            tab_widget = self.media_info_tabs.widget(index)
            if tab_widget is not None:
                tab_widget.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
