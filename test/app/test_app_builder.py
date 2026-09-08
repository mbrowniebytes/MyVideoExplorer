from unittest.mock import Mock

from PySide6.QtWidgets import QApplication, QMainWindow

from MyVideoExplorer.app.app_builder import AppBuilder


def test_create_right_panel_does_not_rewire_shared_views():
    QApplication.instance() or QApplication([])
    window = QMainWindow()
    container = Mock()
    image_list_view = Mock()
    media_info_side_view = object()
    image_list_view.media_info_side_view = media_info_side_view
    container.image_list = Mock()
    container.image_list.image_list_view = image_list_view

    media_info_tabs = Mock()
    expected = Mock()
    media_info_tabs.build.return_value = expected
    container.media_info_tabs = media_info_tabs

    builder = AppBuilder(container, app=None, window=window)

    result = builder._create_right_panel()

    assert result is expected
    assert image_list_view.media_info_side_view is media_info_side_view
