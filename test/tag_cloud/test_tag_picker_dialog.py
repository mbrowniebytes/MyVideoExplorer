from unittest.mock import MagicMock

from PySide6.QtWidgets import QToolButton, QWidget

from MyVideoExplorer.tag_cloud.tag_picker_dialog import TagPickerDialog


def test_tag_picker_dialog_set_data_and_signals(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    dialog = TagPickerDialog(parent)
    qtbot.addWidget(dialog)

    tag_selected = MagicMock()
    tag_removed = MagicMock()
    tag_created = MagicMock()
    dialog.tag_selected.connect(tag_selected)
    dialog.tag_removed.connect(tag_removed)
    dialog.tag_created.connect(tag_created)

    dialog.set_data(
        tags=["Action"],
        tag_colors={"action": "#ff0000", "comedy": "#00ff00"},
        all_catalog_tags=[
            {"tag": "Action", "color": "#ff0000"},
            {"tag": "Comedy", "color": "#00ff00"},
        ],
        tag_counts={"action": 5, "comedy": 10},
    )

    # Current tags row contains Action
    assert dialog.assigned_layout.count() >= 1

    # Remove button in assigned tags
    remove_btn = next(
        btn
        for btn in dialog.assigned_container.findChildren(QToolButton)
        if "Remove Action" in btn.toolTip()
    )
    remove_btn.click()
    tag_removed.assert_called_with("Action")

    # Available tags cloud contains Comedy (since Action is assigned)
    available_tags = [t["tag"] for t in dialog.cloud.tags]
    assert "Comedy" in available_tags
    assert "Action" not in available_tags

    # Test create tag
    dialog.new_tag_edit.setText("SciFi")
    dialog.create_button.click()
    tag_created.assert_called_with("SciFi")


def test_tag_picker_dialog_close_button(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    dialog = TagPickerDialog(parent)
    qtbot.addWidget(dialog)
    dialog.show()

    assert hasattr(dialog, "close_button")
    assert dialog.close_button.isVisible()

    dialog.close_button.click()
    assert not dialog.isVisible()
