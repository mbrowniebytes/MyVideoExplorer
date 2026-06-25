import pytest
from unittest.mock import MagicMock, patch
from MyVideoExplorer.media_info_side.media_info_side_view import MediaInfoSideView
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.utils.str_util import StrUtil


class TestMediaInfoSideView:
    @pytest.fixture
    def mock_nfo_data(self):
        return {
            "title": "Test Movie",
            "year": 2024,
            "plot": "A test plot for a test movie.",
            "genres": ["Action", "Sci-Fi"],
            "actors": [{"name": "Actor A", "role": "Hero"}],
            "director": "Director X",
            "rating": 8.5,
            "runtime": 120,
            "ids": [{"site": "imdb", "id": "tt1234567"}],
        }

    @pytest.fixture
    def media_info_side_view(self, qtbot):
        nfo_parse_util = MagicMock(spec=NfoParseUtil)
        str_util = MagicMock(spec=StrUtil)
        str_util.join_strings.side_effect = lambda items: ", ".join(map(str, items))
        mock_log = MagicMock()

        view = MediaInfoSideView(nfo_parse_util, str_util, mock_log)
        qtbot.addWidget(view)
        return view

    def test_initialization(self, media_info_side_view):
        assert media_info_side_view.nfo_parse_util is not None

    def test_refresh_calls_nfo_parse(self, media_info_side_view, mock_nfo_data):
        media_info_side_view.nfo_parse_util.parse_nfo.return_value = mock_nfo_data

        with patch.object(media_info_side_view, "build_from_movie_info") as mock_build:
            media_info_side_view.refresh("/some/path")
            media_info_side_view.nfo_parse_util.parse_nfo.assert_called_with(
                folder_path="/some/path"
            )
            mock_build.assert_called_with(mock_nfo_data)

    def test_build_from_movie_info(self, media_info_side_view, mock_nfo_data):
        media_info_side_view.build_from_movie_info(mock_nfo_data)

        # Verify plot text
        assert (
            media_info_side_view.plot_section.get_plot_text().toPlainText()
            == mock_nfo_data["plot"]
        )

        # Verify some labels exist
        from PySide6.QtWidgets import QLabel

        labels = media_info_side_view.findChildren(QLabel)
        texts = [label.text() for label in labels]
        assert any("Score" in t for t in texts)
        assert any("8.5" in t for t in texts)

    def test_clear_nfo(self, media_info_side_view, mock_nfo_data):
        media_info_side_view.build_from_movie_info(mock_nfo_data)
        media_info_side_view.clear_nfo()

        from PySide6.QtWidgets import QLabel

        labels = media_info_side_view.findChildren(QLabel)
        texts = [label.text() for label in labels]
        assert any("No NFO data found" in t for t in texts)

    def test_play_video_signal(self, media_info_side_view, mock_nfo_data, qtbot):
        media_info_side_view.build_from_movie_info(mock_nfo_data)

        with qtbot.waitSignal(
            media_info_side_view.sig_info_side_play_video_btn_clicked
        ) as blocker:
            media_info_side_view.play_video()

        assert blocker.signal_triggered

    def test_apply_theme(self, media_info_side_view, mock_nfo_data):
        media_info_side_view.build_from_movie_info(mock_nfo_data)
        media_info_side_view.apply_theme()
        assert media_info_side_view.styleSheet() != ""
