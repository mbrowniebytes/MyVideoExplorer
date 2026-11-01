from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QSizePolicy,
    QWidget,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.utils.ui_utils import UIUtils
from MyVideoExplorer.widgets.buttons.action_button import ActionButton


class FolderPickerWidget(QWidget):
    sig_selected_folder = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self._selected_folder = ""
        self._ui_utils = UIUtils()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = self._ui_utils.apply_compact_layout(self, QHBoxLayout)

        self.pick_button = ActionButton(
            self, icon_name="fa6s.folder-open", tooltip="Select Folder"
        )
        self.pick_button.setCheckable(True)
        self.pick_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.pick_button.setFixedSize(70, 40)

        self.pick_button.setText("")

        self.pick_button.clicked.connect(self.pick_folder)
        layout.addWidget(self.pick_button)

    @property
    def selected_folder(self) -> str:
        return self._selected_folder

    @selected_folder.setter
    def selected_folder(self, value: str) -> None:
        if self._selected_folder == value:
            return
        self._selected_folder = value
        payload = SignalPayload(
            data=value,
            sender=self.__class__.__name__,
            name="Selected Folder Changed",
            description="Emitted when the selected folder changes in FolderPickerWidget.",
            flow=SignalFlow.USER_INPUT,
        )
        self.sig_selected_folder.emit(payload)

    def pick_folder(self) -> None:
        """Open a dialog to select a folder and store the result."""
        selected_folder = QFileDialog.getExistingDirectory(
            self,
            "Select a folder",
            dir=self._selected_folder,
        )
        if not selected_folder:
            return

        # The property setter handles duplicate checks and signal emission automatically
        self.selected_folder = selected_folder
