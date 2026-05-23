import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget
from src.image_list.image_list_view import ImageListView
from src.file_list.file_list import FileList
from src.media_info.media_info_side_view import MediaInfoSideView
from src.utils.str_util import StrUtil
from src.utils.nfo_parse_util import NfoParseUtil

_NO_IMAGE_FOUND = """
    No image found.\n
    Select a folder by Mouse Wheel over this area\n
    or by Selecting a folder in the Folder list to the left.
"""

class TestImageListView:
    @pytest.fixture
    def image_list_view(self, qtbot):
        str_util =  MagicMock(spec=StrUtil)
        nfo_parse_util = MagicMock(spec=NfoParseUtil)
        mock_log = MagicMock()
        side_view = MediaInfoSideView(nfo_parse_util, str_util, mock_log)
        file_list = MagicMock(spec=FileList)
        file_list.build.return_value = QWidget()
        view = ImageListView(str_util, side_view, file_list, mock_log)
        view.build()
        qtbot.addWidget(view)
        return view

    def test_initialization(self, image_list_view):
        assert image_list_view.preview_widget is not None
        assert image_list_view.title_widget is not None
        assert image_list_view.media_info_side_view is not None

    def test_load_pixmap_null(self, image_list_view):
        image_list_view.load_pixmap(None)
        assert image_list_view.preview_widget.image_label.text() == _NO_IMAGE_FOUND

    def test_load_pixmap_valid(self, image_list_view):
        # We need a small real image or a mock that QPixmap can handle.
        # Let's try to mock QPixmap to return not null.
        with patch("src.image_list.image_preview_widget.QPixmap") as mock_pixmap:
            real_pixmap = QPixmap(1, 1)
            mock_pixmap.return_value = real_pixmap
            image_list_view.load_pixmap("/path/to/image.jpg")
            assert (
                image_list_view.title_widget.title_label.text() == "to"
            )  # Based on pathlib.Path(image_path).parent.name
            assert (
                "Image Preview Usage:"
                in image_list_view.title_widget.help_icon.toolTip()
            )
            assert image_list_view.preview_widget._pixmap is not None

    def test_clear_nfo(self, image_list_view):
        with patch.object(
            image_list_view.media_info_side_view, "clear_nfo"
        ) as mock_clear:
            image_list_view.clear_nfo()
            mock_clear.assert_called_once()

    def test_build_nfo(self, image_list_view):
        nfo = {"title": "Movie"}
        with patch.object(
            image_list_view.media_info_side_view, "build_nfo"
        ) as mock_build:
            image_list_view.build_nfo(nfo)
            mock_build.assert_called_with(nfo)

    def test_apply_theme(self, image_list_view):
        with patch("src.image_list.image_list_view.APP_THEME") as mock_theme:
            mock_theme.font_family = "Arial"
            mock_theme.font_size = 12
            mock_theme.container_qss.return_value = "background: black;"
            mock_theme.title_label_qss.return_value = "color: white;"

            with patch.object(
                image_list_view.media_info_side_view, "apply_theme"
            ) as mock_apply:
                image_list_view.apply_theme()
                assert image_list_view.font().family() == "Arial"
                mock_apply.assert_called_once()
