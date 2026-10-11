from unittest.mock import MagicMock

from PySide6.QtWidgets import QToolButton

from MyVideoExplorer.tag_cloud.tag_button import TagButton
from MyVideoExplorer.tag_cloud.tag_picker_dialog import TagPickerDialog


def test_tag_picker_dialog_set_data_and_signals(qtbot):
    dialog = TagPickerDialog()
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

    # Current tags row contains Action with tag count
    assert dialog.assigned_layout.count() >= 1
    assigned_btn = next(
        btn
        for btn in dialog.assigned_container.findChildren(TagButton)
        if btn.text() == "Action (5)"
    )
    assert assigned_btn is not None

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
    assert dialog.new_tag_edit is not None
    assert dialog.create_button is not None
    dialog.new_tag_edit.setText("SciFi")
    dialog.create_button.click()
    tag_created.assert_called_with("SciFi")


def test_tag_picker_dialog_allow_create_false(qtbot):
    dialog = TagPickerDialog(allow_create=False)
    qtbot.addWidget(dialog)

    assert dialog.new_tag_edit is None
    assert dialog.create_button is None
    assert dialog.allow_create is False


def test_tag_picker_dialog_allow_delete_false(qtbot):
    dialog = TagPickerDialog(allow_delete=False)
    qtbot.addWidget(dialog)

    assert dialog.allow_delete is False
    assert dialog.allow_remove is False

    dialog.set_data(
        tags=["Action"],
        tag_colors={"action": "#ff0000"},
        all_catalog_tags=[{"tag": "Action", "color": "#ff0000"}],
        tag_counts={"action": 5},
    )

    # Assigned tag row should have the tag button and color button, but NO trashcan delete button
    assigned_buttons = dialog.assigned_container.findChildren(QToolButton)
    remove_buttons = [
        btn for btn in assigned_buttons if "Remove Action" in btn.toolTip()
    ]
    assert len(remove_buttons) == 0


def test_tag_picker_dialog_dimensions(qtbot):
    dialog = TagPickerDialog()
    qtbot.addWidget(dialog)

    assert dialog.minimumWidth() >= 400
    assert dialog.minimumHeight() >= 300
    assert dialog.sizeHint().width() >= 500
    assert dialog.sizeHint().height() >= 400


def test_tag_picker_dialog_close_button(qtbot):
    dialog = TagPickerDialog()
    qtbot.addWidget(dialog)
    dialog.show()

    assert hasattr(dialog, "close_button")
    assert dialog.close_button.isVisible()

    dialog.close_button.click()
    assert not dialog.isVisible()


def test_tag_picker_dialog_assigned_tags_auto_expands_height(qtbot):
    """Verify that multiple assigned tags wrap in flow layout and expand assigned container height."""
    dialog = TagPickerDialog()
    dialog.resize(500, 400)
    dialog.show()
    qtbot.addWidget(dialog)
    qtbot.waitExposed(dialog)

    # 1 tag assigned
    dialog.set_data(
        tags=["Tag1"],
        tag_colors={"tag1": "#ff0000"},
        all_catalog_tags=[{"tag": "Tag1", "color": "#ff0000"}],
        tag_counts={"tag1": 1},
    )
    single_h = dialog.assigned_container.heightForWidth(400)

    # Multiple tags assigned (should wrap and expand height)
    many_tags = [f"LongTagName{i}" for i in range(12)]
    dialog.set_data(
        tags=many_tags,
        tag_colors={t.casefold(): "#00ff00" for t in many_tags},
        all_catalog_tags=[{"tag": t, "color": "#00ff00"} for t in many_tags],
        tag_counts={t.casefold(): i for i, t in enumerate(many_tags)},
    )
    multi_h = dialog.assigned_container.heightForWidth(400)

    assert multi_h > single_h


def test_tag_picker_dialog_tags_do_not_overlap_after_removal(qtbot):
    """Verify that remaining tags in TagPickerDialog flow naturally and never overlap when a tag is removed."""
    dialog = TagPickerDialog()
    dialog.resize(500, 400)
    dialog.show()
    qtbot.addWidget(dialog)
    qtbot.waitExposed(dialog)

    tags = ["TagAlpha", "TagBeta", "TagGamma", "TagDelta"]
    dialog.set_data(
        tags=tags,
        tag_colors={t.casefold(): "#ff0000" for t in tags},
        all_catalog_tags=[{"tag": t, "color": "#ff0000"} for t in tags],
        tag_counts={t.casefold(): 1 for t in tags},
    )

    def get_assigned_widgets():
        widgets = []
        for i in range(dialog.assigned_layout.count()):
            item = dialog.assigned_layout.itemAt(i)
            if item:
                w = item.widget()
                if w is not None and w.isVisible():
                    widgets.append(w)
        return widgets

    def verify_no_overlap(widgets):
        assert len(widgets) >= 2
        for i in range(len(widgets)):
            for j in range(i + 1, len(widgets)):
                g1 = widgets[i].geometry()
                g2 = widgets[j].geometry()
                assert not g1.intersects(g2), (
                    f"Widget {i} ({g1}) overlaps Widget {j} ({g2})"
                )
                assert g2.y() > g1.y() or (g2.y() == g1.y() and g2.x() >= g1.right())

    # Verify initial 4 tags do not overlap
    initial_widgets = get_assigned_widgets()
    assert len(initial_widgets) == 4
    verify_no_overlap(initial_widgets)

    # Remove second tag ("TagBeta")
    dialog.set_data(
        tags=["TagAlpha", "TagGamma", "TagDelta"],
        tag_colors={t.casefold(): "#ff0000" for t in tags},
        all_catalog_tags=[{"tag": t, "color": "#ff0000"} for t in tags],
        tag_counts={t.casefold(): 1 for t in tags},
    )

    remaining_widgets = get_assigned_widgets()
    assert len(remaining_widgets) == 3
    verify_no_overlap(remaining_widgets)

    # Remove first tag ("TagAlpha")
    dialog.set_data(
        tags=["TagGamma", "TagDelta"],
        tag_colors={t.casefold(): "#ff0000" for t in tags},
        all_catalog_tags=[{"tag": t, "color": "#ff0000"} for t in tags],
        tag_counts={t.casefold(): 1 for t in tags},
    )

    remaining_widgets2 = get_assigned_widgets()
    assert len(remaining_widgets2) == 2
    verify_no_overlap(remaining_widgets2)
