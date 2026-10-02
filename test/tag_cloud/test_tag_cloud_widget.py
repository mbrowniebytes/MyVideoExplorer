from unittest.mock import MagicMock

from PySide6.QtWidgets import QToolButton, QWidget

from MyVideoExplorer.db.models.tag_item import TagItem
from MyVideoExplorer.tag_cloud.tag_cloud_widget import TagCloudWidget


def test_tag_cloud_widget_filter_and_sort(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    widget = TagCloudWidget(
        tags=[
            {"tag": "Zebra", "color": "#111111", "qty": 10},
            {"tag": "Alpha", "color": "#222222", "qty": 50},
            TagItem(tag="Beta", color="#333333", qty=20),
        ],
        selectable=True,
        parent=parent,
    )

    assert len(widget.tags) == 3
    # Default sort A-Z
    chip_texts = [
        chip.findChild(QToolButton).text() for _, chip in widget._tag_widgets
    ]
    assert chip_texts == ["Alpha (50)", "Beta (20)", "Zebra (10)"]

    # Filter
    widget.filter_edit.setText("alp")
    chip_texts = [
        chip.findChild(QToolButton).text() for _, chip in widget._tag_widgets
    ]
    assert chip_texts == ["Alpha (50)"]

    # Clear filter and switch sort to quantity
    widget.filter_edit.clear()
    widget.sort_combo.setCurrentIndex(
        widget.sort_combo.findData(TagCloudWidget.SORT_QUANTITY)
    )
    chip_texts = [
        chip.findChild(QToolButton).text() for _, chip in widget._tag_widgets
    ]
    assert chip_texts == ["Alpha (50)", "Beta (20)", "Zebra (10)"]


def test_tag_cloud_widget_selection(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    widget = TagCloudWidget(
        tags=[
            {"tag": "Drama", "color": "#111111", "qty": 1},
        ],
        selectable=True,
        parent=parent,
    )

    selected_callback = MagicMock()
    widget.tag_selected.connect(selected_callback)

    tag_btn = widget._tag_widgets[0][1].findChild(QToolButton)
    tag_btn.click()
    selected_callback.assert_called_with("Drama", True)
    assert widget.selected_tags == ["Drama"]

    widget.set_selected_tags([])
    assert widget.selected_tags == []
