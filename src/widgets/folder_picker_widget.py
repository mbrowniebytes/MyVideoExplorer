from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFileDialog, QWidget, QHBoxLayout
from src.folder_nav.nav_button import NavButton


class FolderPickerWidget(QWidget):
    sig_selected_folder = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)  # Was missing parent argument
        self._selected_folder = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.pick_button = NavButton("Select Folder", "fa5s.folder-open")
        self.pick_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.pick_button.clicked.connect(self.select_folder)
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

    def pick_folder(self, callback: callable = None) -> None:
        """Open a dialog to select a folder and store the result."""
        selected_folder = QFileDialog.getExistingDirectory(
            self,
            "Select a folder",
            options=QFileDialog.Options(),
            dir=self._selected_folder,
        )
        if not selected_folder:
            return

        if selected_folder != self._selected_folder:
            self.selected_folder = selected_folder

        if callback:
            callback(selected_folder)

    def select_folder(self) -> None:
        self.pick_folder()
