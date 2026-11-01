from __future__ import annotations

from PySide6.QtCore import QElapsedTimer, QEvent, Qt, QTimer
from PySide6.QtGui import QColor, QEnterEvent, QHideEvent, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QMessageBox, QWidget

from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.widgets.buttons.action_button import ActionButton


class DelayedDeleteButton(ActionButton):
    """Delete control that unlocks after a continuous hover delay."""

    DEFAULT_UNLOCK_DELAY_MS = 2500
    DEFAULT_ICON_COLOR = "#6b3030"

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        unlock_delay_ms: int | None = None,
        icon_name: str = "fa6s.trash-can",
        icon_color: str = DEFAULT_ICON_COLOR,
        confirmation_title: str | None = None,
        confirmation_message: str | None = None,
    ) -> None:
        if unlock_delay_ms is None:
            unlock_delay_ms = self.DEFAULT_UNLOCK_DELAY_MS
        if unlock_delay_ms < 0:
            raise ValueError("unlock_delay_ms cannot be negative.")
        if (confirmation_title is None) != (confirmation_message is None):
            raise ValueError(
                "confirmation_title and confirmation_message must be set together."
            )
        self.unlock_delay_ms = unlock_delay_ms
        self.icon_name = icon_name
        self.icon_color = icon_color
        self.confirmation_title = confirmation_title
        self.confirmation_message = confirmation_message
        super().__init__(
            parent,
            icon_name=icon_name,
            icon_color=APP_THEME.config.color_text_muted,
        )
        self._armed = False
        self._hover_elapsed = QElapsedTimer()

        self._unlock_timer = QTimer(self)
        self._unlock_timer.setSingleShot(True)
        self._unlock_timer.setInterval(unlock_delay_ms)
        self._unlock_timer.timeout.connect(self._unlock)
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(250)
        self._progress_timer.timeout.connect(self._update_icon_progress)
        self._set_icon_color(0)
        self._update_locked_state()

    @property
    def is_armed(self) -> bool:
        return self._armed

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        if not self._armed:
            self._hover_elapsed.start()
            self._set_icon_color(0)
            self._unlock_timer.start()
            self._progress_timer.start()

    def leaveEvent(self, event: QEvent) -> None:
        self._unlock_timer.stop()
        self._progress_timer.stop()
        self._lock()
        super().leaveEvent(event)

    def hideEvent(self, event: QHideEvent) -> None:
        self._unlock_timer.stop()
        self._progress_timer.stop()
        self._lock()
        super().hideEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._armed:
            event.ignore()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if not self._armed:
            self.setDown(False)
            event.ignore()
            return
        if (
            self.isDown()
            and self.rect().contains(event.position().toPoint())
            and not self._confirm()
        ):
            self.setDown(False)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def setToolTip(self, text: str) -> None:
        super().setToolTip(text)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._armed and not event.isAutoRepeat():
                self.setDown(True)
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.setDown(False)
            if self._armed and not event.isAutoRepeat():
                self.click()
            event.accept()
            return
        super().keyReleaseEvent(event)

    def click(self) -> None:
        if self._armed and self._confirm():
            super().click()

    def _unlock(self) -> None:
        self._armed = True
        self._progress_timer.stop()
        self._update_locked_state()

    def _lock(self) -> None:
        self._armed = False
        self._update_locked_state()
        self._set_icon_color(0)

    def _update_locked_state(self) -> None:
        self.setProperty("delete_armed", self._armed)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor
            if self._armed
            else Qt.CursorShape.ArrowCursor
        )
        if self._armed:
            self._set_icon_color(1)

    def _update_icon_progress(self) -> None:
        if self.unlock_delay_ms == 0:
            return
        progress = min(self._hover_elapsed.elapsed() / self.unlock_delay_ms, 1)
        self._set_icon_color(progress)

    def _set_icon_color(self, progress: float) -> None:
        start_color = QColor(APP_THEME.config.color_text_muted)
        end_color = QColor(self.icon_color)
        red = round(
            start_color.red() + (end_color.red() - start_color.red()) * progress
        )
        green = round(
            start_color.green() + (end_color.green() - start_color.green()) * progress
        )
        blue = round(
            start_color.blue() + (end_color.blue() - start_color.blue()) * progress
        )
        color = f"#{red:02x}{green:02x}{blue:02x}"
        self.setProperty("delete_icon_color", color)
        self.setIcon(APP_THEME.icon(self.icon_name, color=color))

    def _confirm(self) -> bool:
        if self.confirmation_message is None:
            return True
        return (
            QMessageBox.question(
                self.window(),
                self.confirmation_title or "Confirm deletion",
                self.confirmation_message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )
