
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtWidgets import (
    QFileDialog,
    QWidget,
    QHBoxLayout,
    QToolButton,
    QSizePolicy,
)
from src.app.app_signals_model import SignalPayload, SignalFlow
from src.theme.theme import APP_THEME
from src.widgets.base_widget import BaseWidget


class FolderPickerWidget(BaseWidget):
    sig_selected_folder = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self._selected_folder = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = self.set_compact_layout(QHBoxLayout)

        self.pick_button = QToolButton()
        self.pick_button.setToolTip("Select Folder")
        self.pick_button.setCheckable(True)
        self.pick_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.pick_button.setIcon(APP_THEME.icon("fa5s.folder-open", color=APP_THEME.text_color))
        self.pick_button.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
        self.pick_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.pick_button.setFixedSize(70, 40)

        self.pick_button.setText("")


        self.pick_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
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
            options=QFileDialog.Options(),
            dir=self._selected_folder,
        )
        if not selected_folder:
            return

        # The property setter handles duplicate checks and signal emission automatically
        self.selected_folder = selected_folder

