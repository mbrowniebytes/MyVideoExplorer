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

    container._on_filtered_items(items)

    container.folder_list.populate_view.assert_called_once_with(items)
    container.folder_list.set_selected_folder.assert_called_once_with(expected_folder)
    if expected_folder == current_folder:
        container.controller.set_current_folder.assert_not_called()
    else:
        container.controller.set_current_folder.assert_called_once_with(
            expected_folder, force=True
        )
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
    container.media_nav_search_service = MagicMock()
    container.media_nav_search_service.search.return_value = items

    container._on_media_nav_search_requested(MagicMock())

    container.folder_list.populate_view.assert_called_once_with(items)
    container.folder_list.set_selected_folder.assert_called_once_with(current_folder)
    container.controller.set_current_folder.assert_not_called()
