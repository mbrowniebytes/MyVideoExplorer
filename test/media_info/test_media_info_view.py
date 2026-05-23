import pytest
from unittest.mock import MagicMock, patch
from src.media_info.media_info_view import MediaInfoView
from src.utils.nfo_parse_util import NfoParseUtil
from src.utils.str_util import StrUtil


class TestMediaInfoView:
    @pytest.fixture
    def mock_nfo_data(self):
        return {
            "title": "Test Movie",
            "year": 2024,
            "plot": "A test plot for a test movie.",
            "genres": ["Action", "Sci-Fi"],
            "actors": [
                {"name": "Actor A", "role": "Hero"},
                {"name": "Actor B", "role": "Villain"},
            ],
            "director": "Director X",
            "rating": 8.5,
            "votes": 100,
            "runtime": 120,
            "ids": [{"site": "imdb", "id": "tt1234567"}],
            "videos": [
                {"width": 1920, "height": 1080, "codec": "h264", "aspect": "1.78"}
            ],
            "audios": [{"codec": "ac3", "channels": 6, "language": "eng"}],
            "subtitles": [{"language": "eng"}],
        }

    @pytest.fixture
    def media_info_view(self, qtbot):
        nfo_parse_util = MagicMock(spec=NfoParseUtil)
        str_util = MagicMock(spec=StrUtil)
        # Mock StrUtil methods
        str_util.join_strings.side_effect = lambda items: ", ".join(map(str, items))

        view = MediaInfoView(nfo_parse_util, str_util)
        qtbot.addWidget(view)
        return view

    def test_initialization(self, media_info_view):
        assert media_info_view.nfo_parse_util is not None
        assert media_info_view.view_mode == "media_info"

    def test_refresh_calls_nfo_parse(self, media_info_view, mock_nfo_data):
        media_info_view.nfo_parse_util.parse_nfo.return_value = mock_nfo_data

        with patch.object(media_info_view, "set_movie_info") as mock_set:
            media_info_view.refresh("/some/path")
            media_info_view.nfo_parse_util.parse_nfo.assert_called_with(
                folder_path="/some/path"
            )
            mock_set.assert_called_with(mock_nfo_data)

    def test_build_from_movie_info(self, media_info_view, mock_nfo_data, qtbot):
        media_info_view.build_from_movie_info(mock_nfo_data)

        # Verify some UI elements were created
        assert (
            media_info_view.plot_section.plot_text.toPlainText()
            == mock_nfo_data["plot"]
        )
        # Check if title label was updated
        # The title is in a label inside common_section.
        labels = media_info_view.findChildren(
            pytest.importorskip("PySide6.QtWidgets").QLabel
        )
        titles = [
            label.text()
            for label in labels
            if str(mock_nfo_data["title"]) in label.text()
        ]
        assert len(titles) > 0

    def test_toggle_section(self, media_info_view, mock_nfo_data):
        media_info_view.build_from_movie_info(mock_nfo_data)
        media_info_view.show()

        # Common section should be visible by default
        common_widget = media_info_view.section_widgets.get("section_common")
        assert common_widget is not None
        assert common_widget.isVisible()

        media_info_view._toggle_section("section_common")
        assert not common_widget.isVisible()

        media_info_view._toggle_section("section_common")
        assert common_widget.isVisible()

    def test_play_video_signal(self, media_info_view, mock_nfo_data, qtbot):
        media_info_view.build_from_movie_info(mock_nfo_data)

        with qtbot.waitSignal(
            media_info_view.sig_info_play_video_btn_clicked
        ) as blocker:
            media_info_view.play_video()

        # No args for this signal usually, just verification it was emitted
        assert blocker.signal_triggered

    def test_apply_theme(self, media_info_view, mock_nfo_data):
        media_info_view.build_from_movie_info(mock_nfo_data)
        with patch("src.media_info.media_info_view.APP_THEME") as mock_theme:
            mock_theme.font_family = "Arial"
            mock_theme.font_size = 14
            mock_theme.container_qss.return_value = "background-color: black;"
            mock_theme.small_button_qss.return_value = "color: white;"

            media_info_view.apply_theme()

            assert media_info_view.font().family() == "Arial"
            assert "background-color: black;" in media_info_view.styleSheet()
