from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from MyVideoExplorer.tag_cloud.tag_button import TagButton


def test_tag_button_double_click_signal(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    button = TagButton(parent)
    button.setText("Sample")

    callback = MagicMock()
    button.double_clicked.connect(callback)

    assert button.property("preserve_custom_style") is True

    qtbot.mouseDClick(button, Qt.MouseButton.LeftButton)
    callback.assert_called_once()
