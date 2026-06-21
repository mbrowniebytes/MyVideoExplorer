from MyVideoExplorer.media_info.media_info_toolbar_widget import MediaInfoToolbarWidget
from MyVideoExplorer.media_info_section.media_info_section_definitions import MEDIA_INFO_VIEW_MODE_DEFAULT


def test_toolbar_builds_default_buttons(qtbot):
    toolbar = MediaInfoToolbarWidget()
    qtbot.addWidget(toolbar)

    toolbar.rebuild_for_view_mode(MEDIA_INFO_VIEW_MODE_DEFAULT)

    assert "section_common" in toolbar.section_toggle_buttons_by_id
    assert "section_plot" in toolbar.section_toggle_buttons_by_id
    assert "section_ids" in toolbar.section_toggle_buttons_by_id
    assert "section_actors" in toolbar.section_toggle_buttons_by_id
