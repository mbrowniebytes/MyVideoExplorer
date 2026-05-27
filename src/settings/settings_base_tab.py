from PySide6.QtCore import Signal
from src.theme.theme import APP_THEME
from src.utils.log_util import LogUtil
from src.widgets.base_widget import BaseWidget


class SettingsBaseTab(BaseWidget):
    """Base class for settings tabs to provide standard signaling and save button behavior."""
    sig_changed = Signal()
    sig_saved = Signal()

    def __init__(self, log_util:LogUtil, parent=None):
        super().__init__(log_util, parent)
        self.log_util = log_util
        self.is_dirty = False
        self.save_btn = None

    def _on_setting_changed(self):
        """Emit change signal when a setting is modified."""
        self.sig_changed.emit()

    def highlight_save_button(self):
        """Update save button style and text to indicate unsaved changes."""
        if self.save_btn:
            self.is_dirty = True
            self.save_btn.setStyleSheet(APP_THEME.button_qss() + APP_THEME.button_highlight_qss())
            # Ensure only one indicator suffix is present
            text = self.save_btn.text().removesuffix(" *") + " *"
            self.save_btn.setText(text)

    def reset_save_button(self):
        """Reset save button style and text to default state."""
        if self.save_btn:
            self.is_dirty = False
            self.save_btn.setStyleSheet(APP_THEME.button_qss())
            text = self.save_btn.text().removesuffix(" *")
            self.save_btn.setText(text)
