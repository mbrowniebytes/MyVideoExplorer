from unittest.mock import MagicMock

import pytest

from MyVideoExplorer.file_list.file_list import FileList
from MyVideoExplorer.image_list.image_list import ImageList
from MyVideoExplorer.image_list.image_list_view import ImageListView
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.utils.str_util import StrUtil


class TestImageList:
    @pytest.fixture
    def image_list(self, qtbot):
        file_util = MagicMock(spec=FileUtil)
        settings = MagicMock()
        settings.settings_data_model.media_configs = []
        nfo_parse_util = MagicMock(spec=NfoParseUtil)
        nfo_parse_util.parse_nfo_folder.return_value = {}

        view = MagicMock(spec=ImageListView)
        file_list = MagicMock(spec=FileList)
        mock_log = MagicMock()
        str_util = MagicMock(spec=StrUtil)

        il = ImageList(
            file_util, settings, nfo_parse_util, str_util, view, file_list, mock_log
        )
        il.build()
        return il

    def test_initialization(self, image_list):
        assert image_list.selected_image_index == -1
        assert image_list.images == []

    def test_update_image_from_folder(self, image_list, tmp_path):
        image_list.file_util.get_images_from_folder.return_value = (
            ["img1.jpg", "img2.jpg"],
            "img1.jpg",
        )

        image_list.update_image_from_folder(str(tmp_path))

        assert image_list.images == ["img1.jpg", "img2.jpg"]
        assert image_list.selected_image_path == "img1.jpg"
        image_list.image_list_view.load_pixmap.assert_called_with("img1.jpg")
        image_list.nfo_parse_util.parse_nfo_folder.assert_called_with(str(tmp_path))

    def test_update_image_from_missing_folder_should_show_rescan_message(
        self, image_list, monkeypatch
    ):
        monkeypatch.setattr("pathlib.Path.is_dir", lambda _path: False)
        image_list.image_list_view.show_empty_state.reset_mock()

        image_list.update_image_from_folder("/missing/movie")

        image_list.image_list_view.show_empty_state.assert_called_once()
        message = image_list.image_list_view.show_empty_state.call_args.args[0]
        assert "missing or inaccessible" in message
        assert "Settings → Media" in message
        image_list.file_util.get_images_from_folder.assert_not_called()
        image_list.nfo_parse_util.parse_nfo_folder.assert_not_called()
        assert image_list.selected_image_path == ""
        assert image_list.images == []

    def test_request_next_image(self, image_list, qtbot):
        image_list.images = ["img1.jpg", "img2.jpg"]
        image_list.selected_image_index = 0

        with qtbot.waitSignal(image_list.image_selected_intent) as blocker:
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
