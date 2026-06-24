import pytest
from unittest.mock import MagicMock, patch

from MyVideoExplorer.media_info.media_info_view import MediaInfoView
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.utils.str_util import StrUtil


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
        log_util = MagicMock(spec=LogUtil)
        # Mock StrUtil methods
        str_util.join_strings.side_effect = lambda items: ", ".join(map(str, items))

        view = MediaInfoView(nfo_parse_util, str_util, log_util)
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
        def check_plot_text():
            assert (
                media_info_view.plot_section.get_plot_text().toPlainText()
                == mock_nfo_data["plot"]
            )
        qtbot.waitUntil(check_plot_text, timeout=250)

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

    def test_toggle_section(self, media_info_view, mock_nfo_data, qtbot):
        media_info_view.build_from_movie_info(mock_nfo_data)
        media_info_view.show()

        # Common section should be visible by default
        def check_section_common():
            common_widget = media_info_view.section_widgets.get("section_common")
            assert common_widget is not None
            assert common_widget.isVisible()

            media_info_view._toggle_section("section_common")
            assert not common_widget.isVisible()

            media_info_view._toggle_section("section_common")
            assert common_widget.isVisible()

        qtbot.waitUntil(check_section_common, timeout=250)

    def test_play_video_signal(self, media_info_view, mock_nfo_data, qtbot):
        media_info_view.build_from_movie_info(mock_nfo_data)

        with qtbot.waitSignal(
            media_info_view.sig_info_play_video_btn_clicked
        ) as blocker:
            media_info_view.play_video()

        assert blocker.args[0].data is None

    def test_apply_theme(self, media_info_view, mock_nfo_data):
        media_info_view.build_from_movie_info(mock_nfo_data)
        from MyVideoExplorer.theme.theme import APP_THEME

        # We mock refresh_theme to see if it's called, but we want it to actually run
        # or at least we want to see if apply_theme() sets the font.
        # Actually, if we mock it, the original refresh_theme (which now sets the font)
        # won't run.

        with patch.object(APP_THEME, "refresh_theme", wraps=APP_THEME.refresh_theme) as mock_refresh:
            APP_THEME.config.font_family_default = "Arial"
            APP_THEME.config.font_size_base = 14

            media_info_view.apply_theme()

            mock_refresh.assert_called()
            assert media_info_view.font().pixelSize() == 14
