import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QWidget
from src.media_info_tabs.media_info_tabs import MediaInfoTabs
from src.media_info.media_info import MediaInfo
from src.image_list.image_list import ImageList
from src.settings.settings import Settings


class TestMediaTabs:
    @pytest.fixture
    def media_tabs(self, qtbot):
        mock_log = MagicMock()
        tabs = MediaInfoTabs(mock_log)
        # Mock components to avoid deep build issues
        mock_mi = MagicMock(spec=MediaInfo)
        mock_mi.build.return_value = QWidget()
        mock_il = MagicMock(spec=ImageList)
        mock_il.build.return_value = QWidget()
        mock_settings = MagicMock(spec=Settings)
        mock_settings.build.return_value = QWidget()

        tabs.build(mock_mi, mock_il, mock_settings)
        qtbot.addWidget(tabs)
        return tabs

    def test_initialization(self, media_tabs):
        assert media_tabs.media_info_tabs.count() == 4
        assert media_tabs.media_info_tabs.tabText(0) == "media"
        assert media_tabs.media_info_tabs.tabText(1) == "info"
        assert media_tabs.media_info_tabs.tabText(2) == ""
        assert media_tabs.media_info_tabs.tabText(3) == "⚙"

    def test_tab_changed_emits_signal(self, media_tabs, qtbot):
        with qtbot.waitSignal(media_tabs.sig_tab_click) as blocker:
            media_tabs.media_info_tabs.setCurrentIndex(1)
        assert blocker.args[0] == 1
        assert media_tabs.current_tab == 1

    def test_show_settings_tab(self, media_tabs):
        media_tabs.show_settings_tab()
        assert media_tabs.media_info_tabs.currentIndex() == 3

    def test_spacer_tab_expands(self, media_tabs):
        tab_bar = media_tabs.media_info_tabs.tabBar()
        spacer_index = 2

        # Mock width of the tab bar container
        media_tabs.media_info_tabs.resize(1000, 500)

        size_hint = tab_bar.tabSizeHint(spacer_index)

        # The spacer should be large if total width is 1000
        # Normal tabs are usually around 100px
        assert size_hint.width() > 500

    def test_apply_theme(self, media_tabs):
        with patch("src.media_info_tabs.media_info_tabs.APP_THEME") as mock_theme:
            mock_theme.font_family = "Arial"
            mock_theme.font_size = 12
            mock_theme.tabs_qss.return_value = "QTabWidget { color: red; }"

            media_tabs.apply_theme()
            assert (
                media_tabs.media_info_tabs.styleSheet() == "QTabWidget { color: red; }"
            )
            media_tabs.media_info.apply_theme.assert_called_once()
