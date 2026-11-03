from PySide6.QtCore import Qt

from MyVideoExplorer.folder_list.folder_list_header import FolderListHeader


def test_sort_combo_should_expose_requested_sort_options(qtbot):
    header = FolderListHeader()
    qtbot.addWidget(header)

    combo = header.sort_combo
    assert [combo.itemData(index) for index in (0, 1, 3, 4, 5, 6)] == [
        "default",
        "filter_sort",
        "a_z",
        "z_a",
        "last_played",
        "qty_played",
    ]
    assert combo.itemText(0) == "Default (A-Z)"
    assert combo.itemText(1) == "Filter Sort (Default)"
    assert combo.itemText(2) == "Other"
    assert not header._sort_model.item(2).flags() & Qt.ItemFlag.ItemIsEnabled

    header.set_filter_sort_label("Last Played")
    assert combo.itemText(1) == "Filter Sort (Last Played)"

    with qtbot.waitSignal(header.sort_changed) as blocker:
        combo.setCurrentIndex(5)
    assert blocker.args == ["last_played"]
