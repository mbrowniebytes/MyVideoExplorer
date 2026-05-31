import pytest
from unittest.mock import MagicMock, patch
from src.media_info.media_info import MediaInfo
from src.media_info.media_info_view import MediaInfoView
from src.media_info_side.media_info_side_view import MediaInfoSideView
from src.utils.nfo_parse_util import NfoParseUtil
from src.utils.str_util import StrUtil


class TestMediaInfo:
    @pytest.fixture
    def media_info(self, qtbot):
        nfo_parse_util = MagicMock(spec=NfoParseUtil)
        str_util = MagicMock(spec=StrUtil)
        mock_log = MagicMock()
        view = MediaInfoView(nfo_parse_util, str_util, mock_log)
        side_view = MediaInfoSideView(nfo_parse_util, str_util, mock_log)

        mi = MediaInfo(view, side_view, mock_log)
        mi.build()
        qtbot.addWidget(mi)
        return mi

    def test_build(self, media_info):
        assert media_info.media_info is not None
        assert media_info.media_info_layout is not None
        # Check if media_info_view was added to layout
        # We can't easily check mock in layout, but we know build was called
        pass

    def test_refresh(self, media_info):
        with patch.object(media_info.media_info_view, "refresh") as mock_refresh:
            with patch.object(
                media_info.media_info_side_view, "refresh"
            ) as mock_side_refresh:
                media_info.refresh("/test/path", 1)
                assert media_info.folder_path == "/test/path"
                mock_refresh.assert_called_with(folder_path="/test/path")
                mock_side_refresh.assert_called_with(folder_path="/test/path")

    def test_play_video_signal_forwarding_from_view(self, media_info, qtbot):
        with qtbot.waitSignal(media_info.sig_play_video) as blocker:
            media_info.media_info_view.sig_info_play_video_btn_clicked.emit()
        assert blocker.signal_triggered

    def test_play_video_signal_forwarding_from_side_view(self, media_info, qtbot):
        with qtbot.waitSignal(media_info.sig_play_video) as blocker:
            media_info.media_info_side_view.sig_info_side_play_video_btn_clicked.emit()
        assert blocker.signal_triggered

    def test_apply_theme(self, media_info):
        with patch.object(media_info.media_info_view, "apply_theme") as mock_view_theme:
            with patch.object(
                media_info.media_info_side_view, "apply_theme"
            ) as mock_side_theme:
                media_info.apply_theme()
                mock_view_theme.assert_called_once()
                mock_side_theme.assert_called_once()
