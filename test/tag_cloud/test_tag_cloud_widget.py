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
        btn.text()
        for _, chip in widget._tag_widgets
        if (btn := chip.findChild(QToolButton)) is not None
    ]
    assert chip_texts == ["Alpha (50)", "Beta (20)", "Zebra (10)"]

    # Filter
    widget.filter_edit.setText("alp")
    chip_texts = [
        btn.text()
        for _, chip in widget._tag_widgets
        if (btn := chip.findChild(QToolButton)) is not None
    ]
    assert chip_texts == ["Alpha (50)"]

    # Clear filter and switch sort to quantity
    widget.filter_edit.clear()
    widget.sort_combo.setCurrentIndex(
        widget.sort_combo.findData(TagCloudWidget.SORT_QUANTITY)
    )
    chip_texts = [
        btn.text()
        for _, chip in widget._tag_widgets
        if (btn := chip.findChild(QToolButton)) is not None
    ]
    assert chip_texts == ["Alpha (50)", "Beta (20)", "Zebra (10)"]


def test_tag_cloud_widget_custom_font_sizes(qtbot):
    """Custom min/max font sizes should produce font sizes within the specified range."""
    parent = QWidget()
    qtbot.addWidget(parent)
    widget = TagCloudWidget(
        tags=[
            {"tag": "Small", "color": "#111111", "qty": 1},
            {"tag": "Medium", "color": "#222222", "qty": 25},
            {"tag": "Large", "color": "#333333", "qty": 100},
        ],
        min_font_size=12,
        max_font_size=32,
        parent=parent,
    )

    assert widget.min_font_size == 12
    assert widget.max_font_size == 32

    font_sizes = []
    for _, chip in widget._tag_widgets:
        btn = chip.findChild(QToolButton)
        if btn is not None:
            font_sizes.append(btn.font().pointSize())

    # All font sizes should be within [12, 32]
    for size in font_sizes:
        assert 12 <= size <= 32, f"Font size {size} out of range [12, 32]"

    # With A-Z sort: Large(100), Medium(25), Small(1)
    # The largest qty tag should have a larger font than the smallest qty tag
    assert font_sizes[0] > font_sizes[2], (
        f"Large tag font ({font_sizes[0]}) should be larger than Small tag font ({font_sizes[2]})"
    )


def test_tag_cloud_widget_default_font_sizes(qtbot):
    """Default font sizes should match class constants."""
    parent = QWidget()
    qtbot.addWidget(parent)
    widget = TagCloudWidget(
        tags=[{"tag": "Test", "color": "#111111", "qty": 1}],
        parent=parent,
    )

    assert widget.min_font_size == TagCloudWidget.MIN_FONT_SIZE
    assert widget.max_font_size == TagCloudWidget.MAX_FONT_SIZE


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
    assert tag_btn is not None
    tag_btn.click()
    selected_callback.assert_called_with("Drama", True)
    assert widget.selected_tags == ["Drama"]

    widget.set_selected_tags([])
    assert widget.selected_tags == []
