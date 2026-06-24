from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton, QWidget

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.base_widget import BaseWidget


class SettingsBaseTab(BaseWidget):
    """Base class for settings tabs to provide standard signaling and save button behavior."""

    sig_changed = Signal(object)
    sig_saved = Signal(object)

    def __init__(
        self, log_util: LogUtil | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(log_util, parent)
        self.log_util = log_util
        self.is_dirty: bool = False
        self.save_btn: QPushButton | None = None
        self.reset_btn: QPushButton | None = None

    def _on_setting_changed(self) -> None:
        """Emit change signal when a setting is modified."""
        payload = SignalPayload(
            data=None,
            sender=self.__class__.__name__,
            name="Setting Changed",
            description="Emitted when a setting is changed in the tab.",
            flow=SignalFlow.USER_INPUT,
        )
        self.sig_changed.emit(payload)
        self.highlight_save_button()

    def _build_reset_button(
        self, label: str, callback: Callable[[], None]
    ) -> QPushButton:
        self.reset_btn = QPushButton(label)
        self.reset_btn.setStyleSheet(APP_THEME.button_qss())
        self.reset_btn.clicked.connect(callback)
        self.reset_btn.setEnabled(False)
        return self.reset_btn

    def reset_settings(self) -> None:
        """Reset settings for this tab."""
        raise NotImplementedError("Subclasses must implement reset_settings")

    def apply_theme(self) -> None:
        # super().apply_theme()
        # Custom logic for highlight state
        if self.save_btn:
            if self.is_dirty:
                self.save_btn.setStyleSheet(
                    APP_THEME.button_qss() + APP_THEME.button_highlight_qss()
                )
            else:
                self.save_btn.setStyleSheet(APP_THEME.button_qss())

    def highlight_save_button(self) -> None:
        """Update save button style and text to indicate unsaved changes."""
        if self.save_btn:
            self.is_dirty = True
            self.save_btn.setStyleSheet(
                APP_THEME.button_qss() + APP_THEME.button_highlight_qss()
            )
            # Ensure only one indicator suffix is present
            text = self.save_btn.text().removesuffix(" *") + " *"
            self.save_btn.setText(text)

        if self.reset_btn:
            self.reset_btn.setEnabled(True)

    def reset_save_button(self) -> None:
        """Reset save button style and text to default state."""
        if self.save_btn:
            self.is_dirty = False
            self.save_btn.setStyleSheet(APP_THEME.button_qss())
            text = self.save_btn.text().removesuffix(" *")
            self.save_btn.setText(text)

        if self.reset_btn:
            self.reset_btn.setEnabled(False)
