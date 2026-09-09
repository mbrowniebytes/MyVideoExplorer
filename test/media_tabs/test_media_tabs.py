import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QWidget
from MyVideoExplorer.media_info_tabs.media_info_tabs import MediaInfoTabs
from MyVideoExplorer.media_info.media_info import MediaInfo
from MyVideoExplorer.image_list.image_list import ImageList
from MyVideoExplorer.settings.settings import Settings


class TestMediaTabs:
    @pytest.fixture
    def media_tabs(self, qtbot):
        mock_log = MagicMock()
        # Mock components to avoid deep build issues
        mock_mi = MagicMock(spec=MediaInfo)
        mock_mi.build.return_value = QWidget()
        mock_il = MagicMock(spec=ImageList)
        mock_il.build.return_value = QWidget()
        mock_settings = MagicMock(spec=Settings)
        mock_settings.build.return_value = QWidget()
        tabs = MediaInfoTabs(mock_log, mock_mi, mock_il, mock_settings)

        tabs.build()
        qtbot.addWidget(tabs)
        return tabs

    def test_initialization(self, media_tabs):
        assert media_tabs.tab_container.count() == 4
        assert media_tabs.tab_container.tabText(0) == "media"
        assert media_tabs.tab_container.tabText(1) == "info"
        assert media_tabs.tab_container.tabText(2) == ""
        assert media_tabs.tab_container.tabText(3) == ""

    def test_tab_changed_emits_signal(self, media_tabs, qtbot):
        with qtbot.waitSignal(media_tabs.tab_selection_changed) as blocker:
            media_tabs.tab_container.setCurrentIndex(1)
        assert blocker.args[0] == 1
        assert media_tabs.active_tab_index == 1

    def test_show_settings_tab(self, media_tabs):
        media_tabs.show_settings_tab()
        assert media_tabs.tab_container.currentIndex() == 3

    def test_spacer_tab_expands(self, media_tabs):
        # Verify spacer tab exists and is disabled as per implementation
        assert media_tabs.tab_container.isTabEnabled(2) is False
        assert media_tabs.tab_container.tabText(2) == ""

    def test_apply_theme(self, media_tabs):
        with patch(
            "MyVideoExplorer.media_info_tabs.media_info_tabs.APP_THEME"
        ) as mock_theme:
            mock_theme.font_family = "Arial"
            mock_theme.font_size = 12
            mock_theme.tabs_qss.return_value = "QTabWidget { color: red; }"

            media_tabs.apply_theme()
            assert media_tabs.tab_container.styleSheet() == "QTabWidget { color: red; }"
            media_tabs.media_info.apply_theme.assert_called()
