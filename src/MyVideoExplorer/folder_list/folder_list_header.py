from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.widgets.buttons.action_button import ActionButton


class FolderListHeader(QWidget, ThemableMixin):
    backward_clicked = Signal()
    clear_filter_clicked = Signal()
    forward_clicked = Signal()
    random_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title_label = QLabel("Folders", parent=self)
        self.help_icon = QLabel("?", parent=self)
        self.backward_folder_button = self._create_nav_folder_button("backward")
        self.clear_filter_button = self._create_clear_filter_button()
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

        layout.addWidget(self.clear_filter_button)
        layout.addWidget(self.backward_folder_button)
        layout.addWidget(self.forward_folder_button)
        layout.addWidget(self.random_folder_button)

    def _create_clear_filter_button(self) -> ActionButton:
        button = ActionButton(
            self,
            icon_name="fa6s.filter-circle-xmark",
            tooltip="Clear Filter and Search",
        )
        button.setFixedSize(30, 30)
        button.setEnabled(False)
        button.clicked.connect(self.clear_filter_clicked)
        return button

    def _create_nav_folder_button(self, direction: str) -> ActionButton:
        button = ActionButton(self, icon_size=APP_THEME.icon_size)
        button.setFixedSize(30, 30)
        button.setEnabled(False)

        if direction == "backward":
            button.set_action_icon("fa6s.reply")
            button.setToolTip("Previous folder")
            button.clicked.connect(self.backward_clicked)
        elif direction == "forward":
            button.set_action_icon("fa6s.share")
            button.setToolTip("Next folder")
            button.clicked.connect(self.forward_clicked)
        elif direction == "random":
            button.set_action_icon("fa6s.dice")
            button.setToolTip("Random folder")
            button.clicked.connect(self.random_clicked)

        return button

    def apply_theme(self):
        self.title_label.setStyleSheet(APP_THEME.label_qss())
        self.help_icon.setStyleSheet(APP_THEME.help_icon_label_qss())
