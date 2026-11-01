from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QPushButton, QWidget

from MyVideoExplorer.widgets.buttons.delayed_delete_button import DelayedDeleteButton


def _send_hover_event(button, event_type: QEvent.Type) -> None:
    if event_type == QEvent.Type.Enter:
        event = QEnterEvent(QPointF(1, 1), QPointF(1, 1), QPointF(1, 1))
        button.enterEvent(event)
    else:
        button.leaveEvent(QEvent(event_type))


def test_delete_button_unlocks_after_continuous_hover_and_relocks_on_leave(qtbot):
    host = QWidget()
    layout = QHBoxLayout(host)
    button = DelayedDeleteButton(unlock_delay_ms=80)
    other = QPushButton("Other")
    layout.addWidget(button)
    layout.addWidget(other)
    qtbot.addWidget(host)
    host.show()
    clicked = []
    button.clicked.connect(lambda: clicked.append(True))

    button.click()
    assert not button.is_armed
    assert button.cursor().shape() == Qt.CursorShape.ArrowCursor
    assert clicked == []
    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
    assert clicked == []

    _send_hover_event(button, QEvent.Type.Enter)
    qtbot.wait(35)
    assert not button.is_armed
    _send_hover_event(button, QEvent.Type.Leave)
    qtbot.wait(65)
    assert not button.is_armed

    _send_hover_event(button, QEvent.Type.Enter)
    qtbot.waitUntil(lambda: button.is_armed, timeout=300)
    assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor
    button.click()
    assert clicked == [True]

    _send_hover_event(button, QEvent.Type.Leave)
    assert not button.is_armed


def test_delete_button_confirmation_is_optional_and_can_cancel(qtbot, monkeypatch):
    button = DelayedDeleteButton(
        unlock_delay_ms=10,
        confirmation_title="Confirm removal",
        confirmation_message="Remove this item?",
    )
    qtbot.addWidget(button)
    button.show()
    _send_hover_event(button, QEvent.Type.Enter)
    qtbot.waitUntil(lambda: button.is_armed, timeout=300)
    clicked = []
    button.clicked.connect(lambda: clicked.append(True))
    responses = iter(
        [
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        ]
    )
    monkeypatch.setattr(
        "MyVideoExplorer.widgets.buttons.delayed_delete_button.QMessageBox.question",
        lambda *_args, **_kwargs: next(responses),
    )

    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
    assert clicked == []
    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
    assert clicked == [True]


def test_delete_button_uses_configurable_icon_and_changes_color_during_delay(
    qtbot, monkeypatch
):
    from PySide6.QtGui import QColor

    monkeypatch.setattr(DelayedDeleteButton, "DEFAULT_UNLOCK_DELAY_MS", 2200)
    button = DelayedDeleteButton(icon_name="fa6s.circle")
    qtbot.addWidget(button)
    button.show()
    button.setToolTip("Delete item")
    initial_color = button.property("delete_icon_color")
    assert button.toolTip() == "Delete item"
    assert button.icon_name == "fa6s.circle"
    assert button.icon_color == DelayedDeleteButton.DEFAULT_ICON_COLOR
    assert button.cursor().shape() == Qt.CursorShape.ArrowCursor

    _send_hover_event(button, QEvent.Type.Enter)
    qtbot.wait(1100)

    intermediate_color = button.property("delete_icon_color")
    assert intermediate_color != initial_color
    assert QColor(intermediate_color) != QColor(button.icon_color)
    assert QColor(intermediate_color).green() < QColor(initial_color).green()
    assert QColor(intermediate_color).blue() < QColor(initial_color).blue()
    assert not button.is_armed

    qtbot.waitUntil(lambda: button.is_armed, timeout=1500)
    assert button.property("delete_icon_color").lower() == button.icon_color.lower()
    assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_delete_button_rejects_partial_confirmation_configuration():
    try:
        DelayedDeleteButton(confirmation_title="Confirm removal")
    except ValueError as error:
        assert "must be set together" in str(error)
    else:
        raise AssertionError("Expected incomplete confirmation configuration to fail.")
