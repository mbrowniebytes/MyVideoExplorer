import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from MyVideoExplorer.widgets.collapsible_box_widget import CollapsibleBoxWidget


class TestCollapsibleBox:
    @pytest.fixture
    def collapsible_box(self, qtbot):
        box = CollapsibleBoxWidget("Collapse Me")
        qtbot.addWidget(box)
        return box

    def test_initialization(self, collapsible_box):
        collapsible_box.show()
        assert collapsible_box.label == "Collapse Me"
        assert collapsible_box.toggle_button.text() == "Collapse Me"
        assert collapsible_box.content_area.isVisible()

    def test_toggle_collapsed_state(self, collapsible_box, qtbot):
        collapsible_box.show()
        # Click toggle button
        qtbot.mouseClick(collapsible_box.toggle_button, Qt.LeftButton)
        assert not collapsible_box.content_area.isVisible()

        qtbot.mouseClick(collapsible_box.toggle_button, Qt.LeftButton)
        assert collapsible_box.content_area.isVisible()

    def test_add_widget(self, collapsible_box):
        widget = QLabel("Inside Content")
        collapsible_box.add_widget(widget)

        # Verify widget is added to content_area's layout
        layout = collapsible_box.content_area.layout()
        assert layout.count() == 1
        assert layout.itemAt(0).widget() == widget

    def test_apply_theme(self, collapsible_box):
        collapsible_box.apply_theme()
        assert collapsible_box.font().family() != ""
