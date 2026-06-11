import pytest
from unittest.mock import MagicMock
from src.image_list.image_list import ImageList
from src.file_list.file_list import FileList
from src.image_list.image_list_view import ImageListView
from src.utils.file_util import FileUtil
from src.utils.nfo_parse_util import NfoParseUtil
from src.utils.str_util import StrUtil


class TestImageList:
    @pytest.fixture
    def image_list(self, qtbot):
        file_util = MagicMock(spec=FileUtil)
        nfo_parse_util = MagicMock(spec=NfoParseUtil)
        nfo_parse_util.parse_nfo_folder.return_value = {}

        view = MagicMock(spec=ImageListView)
        file_list = MagicMock(spec=FileList)
        mock_log = MagicMock()
        str_util = MagicMock(spec=StrUtil)

        il = ImageList(file_util, nfo_parse_util, str_util, view, file_list, mock_log)
        il.build()
        return il

    def test_initialization(self, image_list):
        assert image_list.selected_image_index == -1
        assert image_list.images == []

    def test_update_image_from_folder(self, image_list):
        image_list.file_util.get_images_from_folder.return_value = (
            ["img1.jpg", "img2.jpg"],
            "img1.jpg",
        )

        image_list.update_image_from_folder("/test/folder")

        assert image_list.images == ["img1.jpg", "img2.jpg"]
        assert image_list.selected_image_path == "img1.jpg"
        image_list.image_list_view.load_pixmap.assert_called_with("img1.jpg")
        image_list.nfo_parse_util.parse_nfo_folder.assert_called_with("/test/folder")

    def test_request_next_image(self, image_list, qtbot):
        image_list.images = ["img1.jpg", "img2.jpg"]
        image_list.selected_image_index = 0

        with qtbot.waitSignal(image_list.sig_image_selected_intent) as blocker:
            image_list.request_next_image(1)

        assert blocker.args[0].data == "img2.jpg"
        assert image_list.selected_image_index == 1
        assert image_list.selected_image_path == "img2.jpg"
        image_list.image_list_view.load_pixmap.assert_called_with("img2.jpg")

    def test_request_next_image_wrap(self, image_list):
        image_list.images = ["img1.jpg", "img2.jpg"]
        image_list.selected_image_index = 1

        image_list.request_next_image(1)

        assert image_list.selected_image_index == 0
        assert image_list.selected_image_path == "img1.jpg"

    def test_set_selected_image_empty(self, image_list):
        image_list.set_selected_image("")
        assert image_list.selected_image_path == ""
        image_list.image_list_view.load_pixmap.assert_called_with(None)

    def test_apply_theme(self, image_list):
        image_list.apply_theme()
        image_list.image_list_view.apply_theme.assert_called_once()
