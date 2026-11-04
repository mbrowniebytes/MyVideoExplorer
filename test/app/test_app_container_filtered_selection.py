from unittest.mock import MagicMock

import pytest

from MyVideoExplorer.app.app_container import AppContainer
from MyVideoExplorer.utils.file_util_model import FileUtilModel


@pytest.mark.parametrize(
    ("current_folder", "items", "expected_folder"),
    [
        (
            "/media/Second",
            [
                FileUtilModel(type="dir", name="First", full_path="/media/First"),
                FileUtilModel(type="dir", name="Second", full_path="/media/Second"),
            ],
            "/media/Second",
        ),
        (
            "/media/Removed",
            [
                FileUtilModel(type="dir", name="Second", full_path="/media/Second"),
                FileUtilModel(type="dir", name="First", full_path="/media/First"),
            ],
            "/media/First",
        ),
    ],
)
def test_filtered_items_preserve_selection_or_choose_first_folder(
    current_folder, items, expected_folder
):
    container = AppContainer.__new__(AppContainer)
    container.controller = MagicMock()
    container.controller.state.current_folder = current_folder
    container.folder_list = MagicMock()
    container.settings = MagicMock()
    container.settings.settings_data_model.auto_select_folder = (
        "auto_select_prior_folder"
    )
    container.settings.settings_data_model.prior_folder = "/media/SavedPrior"
    container.log_util = MagicMock()
    container.image_list = MagicMock()
    container.file_list = MagicMock()

    container._on_filtered_items(items)

    container.folder_list.populate_view.assert_called_once_with(items)
    container.folder_list.set_selected_folder.assert_called_once_with(expected_folder)
    if expected_folder == current_folder:
        container.controller.set_current_folder.assert_not_called()
    else:
        container.controller.set_current_folder.assert_called_once_with(
            expected_folder, force=True
        )
    container.file_list.refresh.assert_called_once_with(expected_folder)
    container.image_list.refresh.assert_called_once_with(expected_folder)
    container.image_list.update_image_from_folder.assert_not_called()


def test_search_results_preserve_current_folder_when_present():
    current_folder = "/media/Second"
    items = [
        FileUtilModel(type="dir", name="First", full_path="/media/First"),
        FileUtilModel(type="dir", name="Second", full_path="/media/Second"),
    ]
    container = AppContainer.__new__(AppContainer)
    container.controller = MagicMock()
    container.controller.state.current_folder = current_folder
    container.folder_list = MagicMock()
    container.log_util = MagicMock()
    container.image_list = MagicMock()
    container.file_list = MagicMock()
    container.media_nav_search_service = MagicMock()
    container.media_nav_search_service.search.return_value = items

    container._on_media_nav_search_requested(MagicMock())

    container.folder_list.populate_view.assert_called_once_with(items)
    container.folder_list.set_selected_folder.assert_called_once_with(current_folder)
    container.controller.set_current_folder.assert_not_called()
    container.file_list.refresh.assert_called_once_with(current_folder)
    container.image_list.refresh.assert_called_once_with(current_folder)


@pytest.mark.parametrize("configured_player", [None, "vlc"])
def test_enqueue_playlist_uses_filtered_video_results(configured_player):
    container = AppContainer.__new__(AppContainer)
    container.folder_list = MagicMock()
    container.folder_list.folder_list_view.count.return_value = 3
    folder_items = []
    for path in ("/media/Zulu", "/media/Alpha", "/media/Beta"):
        folder_item = MagicMock()
        folder_item.data.return_value = path
        folder_items.append(folder_item)
    container.folder_list.folder_list_view.item.side_effect = folder_items
    container.folder_nav_filters = MagicMock()
    container.folder_nav_filters.filter_table.collect_filters.return_value = [
        {"filter": "genre", "value": "Action"}
    ]
    container.folder_nav_filters.media_filter_widget.collect_filters.return_value = [
        {"filter": "media", "value": ["/media/Movies"]}
    ]
    filtered_videos = [
        {"file_path": "/media/Zulu/First Movie.mkv"},
        {"file_path": "/media/Alpha/Nested/Second Movie.mp4"},
        {"file_path": "/media/Beta/Third Movie.mkv"},
    ]
    container.folder_nav_filters.db_filter.matching_videos.return_value = (
        filtered_videos
    )
    container.settings = MagicMock()
    container.settings.settings_data_model.video_player_configs = (
        [
            {
                "is_default": True,
                "id": "vlc",
                "executable": "/players/vlc",
                "arguments": "--fullscreen",
            }
        ]
        if configured_player
        else []
    )
    container.video_player = MagicMock()
    container.log_util = MagicMock()

    container._enqueue_filtered_playlist()

    filters = [
        {"filter": "genre", "value": "Action"},
        {"filter": "media", "value": ["/media/Movies"]},
    ]
    container.folder_nav_filters.db_filter.matching_videos.assert_called_once_with(
        filters
    )
    video_paths = [
        "/media/Zulu/First Movie.mkv",
        "/media/Alpha/Nested/Second Movie.mp4",
        "/media/Beta/Third Movie.mkv",
    ]
    if configured_player:
        container.video_player.enqueue_video_paths.assert_called_once_with(
            video_paths, "/players/vlc", "--fullscreen"
        )
    else:
        container.video_player.enqueue_video_paths.assert_called_once_with(video_paths)
