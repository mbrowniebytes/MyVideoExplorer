from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit

from MyVideoExplorer.widgets.name_widget import NameWidget


def _trigger_editing_finished(widget: NameWidget, qtbot) -> None:
    """Focus the widget and press Enter to fire editingFinished."""
    qtbot.keyClick(widget, Qt.Key.Key_Return)


def test_name_widget_valid_name_clears_error(qtbot):
    """A valid name should clear the tooltip and error border."""
    widget = NameWidget()
    qtbot.add_widget(widget)

    widget.setText("ValidName")
    _trigger_editing_finished(widget, qtbot)

    assert widget.toolTip() == ""
    assert widget.styleSheet() == ""


def test_name_widget_invalid_name_shows_error(qtbot):
    """An invalid name (with slashes) should set tooltip and error border."""
    widget = NameWidget()
    qtbot.add_widget(widget)

    widget.setText("path/to")
    _trigger_editing_finished(widget, qtbot)

    assert widget.toolTip() != ""
    assert "border" in widget.styleSheet()
    assert "#8b3b3b" in widget.styleSheet()


def test_name_widget_empty_name_shows_error(qtbot):
    """An empty name should set tooltip and error border."""
    widget = NameWidget()
    qtbot.add_widget(widget)

    widget.setText("")
    _trigger_editing_finished(widget, qtbot)

    assert widget.toolTip() != ""
    assert "cannot be empty" in widget.toolTip()


def test_name_widget_is_qlineedit_subclass():
    """NameWidget should be a QLineEdit subclass for API compatibility."""
    assert issubclass(NameWidget, QLineEdit)


def test_name_widget_quote_rejection(qtbot):
    """A name with quotes should be rejected on blur."""
    widget = NameWidget()
    qtbot.add_widget(widget)

    widget.setText("it's")
    _trigger_editing_finished(widget, qtbot)

    assert widget.toolTip() != ""
    assert "#8b3b3b" in widget.styleSheet()
