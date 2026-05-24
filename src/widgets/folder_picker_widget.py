
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFileDialog, QWidget, QHBoxLayout
from src.folder_nav.nav_button import NavButton
from src.widgets.base_widget import BaseWidget


class FolderPickerWidget(BaseWidget):
    sig_selected_folder = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self._selected_folder = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = self.set_compact_layout(QHBoxLayout)
        self.pick_button = NavButton("Select Folder", "fa5s.folder-open")
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
        self.sig_selected_folder.emit(value)

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

