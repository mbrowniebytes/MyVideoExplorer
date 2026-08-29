from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.theme.themable_mixin import ThemableMixin

class FolderListHeader(QWidget, ThemableMixin):
    sig_backward_clicked = Signal()
    sig_forward_clicked = Signal()
    sig_random_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title_label = QLabel("Folders")
        self.help_icon = QLabel("?")
        self.backward_folder_button = self._create_nav_folder_button("backward")
        self.forward_folder_button = self._create_nav_folder_button("forward")
        self.random_folder_button = self._create_nav_folder_button("random")
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_label.setStyleSheet(APP_THEME.label_qss())

        self.help_icon.setStyleSheet(APP_THEME.help_icon_label_qss())
        self.help_icon.setFixedSize(16, 16)
        self.help_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.title_label)
        layout.addWidget(self.help_icon)
        layout.addStretch()

        layout.addWidget(self.backward_folder_button)
        layout.addWidget(self.forward_folder_button)
        layout.addWidget(self.random_folder_button)

    def _create_nav_folder_button(self, direction: str) -> QToolButton:
        button = QToolButton()
        button.setFixedSize(30, 30)
        button.setStyleSheet(APP_THEME.button_qss())
        button.setEnabled(False)

        if direction == "backward":
            button.setIcon(APP_THEME.icon("fa5s.arrow-left"))
            button.setToolTip("Backward")
            button.clicked.connect(self.sig_backward_clicked)
        elif direction == "forward":
            button.setIcon(APP_THEME.icon("fa5s.arrow-right"))
            button.setToolTip("Forward")
            button.clicked.connect(self.sig_forward_clicked)
        elif direction == "random":
            button.setIcon(APP_THEME.icon("fa5s.random"))
            button.setToolTip("Random")
            button.clicked.connect(self.sig_random_clicked)

        return button

    def apply_theme(self):
        self.title_label.setStyleSheet(APP_THEME.label_qss())
        self.help_icon.setStyleSheet(APP_THEME.help_icon_label_qss())
        self.backward_folder_button.setStyleSheet(APP_THEME.button_qss())
        self.forward_folder_button.setStyleSheet(APP_THEME.button_qss())
        self.random_folder_button.setStyleSheet(APP_THEME.button_qss())
