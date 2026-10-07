from PySide6.QtCore import QRect
from PySide6.QtWidgets import QLabel, QWidget

from MyVideoExplorer.widgets.flow_layout import FlowLayout


def test_flow_layout_item_management(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    layout = FlowLayout(parent, spacing=6)

    lbl1 = QLabel("Item 1")
    lbl2 = QLabel("Item 2")
    lbl3 = QLabel("Item 3")

    layout.addWidget(lbl1)
    layout.addWidget(lbl2)
    layout.addWidget(lbl3)

    assert layout.count() == 3
    item0 = layout.itemAt(0)
    assert item0 is not None
    assert item0.widget() == lbl1
    item1 = layout.itemAt(1)
    assert item1 is not None
    assert item1.widget() == lbl2
    item2 = layout.itemAt(2)
    assert item2 is not None
    assert item2.widget() == lbl3
    assert layout.itemAt(3) is None

    taken = layout.takeAt(1)
    assert taken is not None
    assert taken.widget() == lbl2
    assert layout.count() == 2
    item1_after = layout.itemAt(1)
    assert item1_after is not None
    assert item1_after.widget() == lbl3


def test_flow_layout_size_hint_and_height_for_width(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    layout = FlowLayout(parent, spacing=8)

    for i in range(5):
        lbl = QLabel(f"Label {i}")
        lbl.setFixedSize(100, 30)
        layout.addWidget(lbl)

    assert layout.hasHeightForWidth() is True
    # At wide width, items fit on 1 row
    height_wide = layout.heightForWidth(600)
    # At narrow width, items must wrap to multiple rows
    height_narrow = layout.heightForWidth(150)
    assert height_narrow > height_wide

    size_hint = layout.sizeHint()
    assert size_hint.width() >= 100
    assert size_hint.height() >= 30


def test_flow_layout_set_geometry(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    layout = FlowLayout(parent, spacing=4)

    lbl1 = QLabel("1")
    lbl1.setFixedSize(50, 20)
    lbl2 = QLabel("2")
    lbl2.setFixedSize(50, 20)
    layout.addWidget(lbl1)
    layout.addWidget(lbl2)

    layout.setGeometry(QRect(0, 0, 200, 100))
    assert lbl1.geometry().x() >= 0
    assert lbl2.geometry().x() > lbl1.geometry().x()
