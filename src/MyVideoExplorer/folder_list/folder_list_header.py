from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from MyVideoExplorer.lang.lang_en import LangEn
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.widgets.buttons.action_button import ActionButton
from MyVideoExplorer.widgets.combo_boxes.select_combo_box import SelectComboBox


class FolderListHeader(QWidget, ThemableMixin):
    backward_clicked = Signal()
    clear_filter_clicked = Signal()
    enqueue_playlist_requested = Signal()
    forward_clicked = Signal()
    random_clicked = Signal()
    sort_changed = Signal(str)

    def __init__(self, lang: LangEn, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.title_label = QLabel(self.lang.ui.folder_list.title, parent=self)
        self.help_icon = QLabel("?", parent=self)
        self._sort_model = QStandardItemModel(self)
        self.sort_combo = self._create_sort_combo()
        self.enqueue_playlist_button = self._create_enqueue_playlist_button()
        self.backward_folder_button = self._create_nav_folder_button("backward")
        self.clear_filter_button = self._create_clear_filter_button()
        self.forward_folder_button = self._create_nav_folder_button("forward")
        self.random_folder_button = self._create_nav_folder_button("random")
        self._build()

    def _build(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        self.title_label.setStyleSheet(APP_THEME.label_qss())

        self.help_icon.setStyleSheet(APP_THEME.help_icon_label_qss())
        self.help_icon.setFixedSize(16, 16)
        self.help_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Row 1: Title, help icon, stretch, nav buttons
        row1 = QHBoxLayout()
        row1.addWidget(self.title_label)
        row1.addWidget(self.help_icon)
        row1.addStretch()
        row1.addWidget(self.clear_filter_button)
        row1.addWidget(self.backward_folder_button)
        row1.addWidget(self.forward_folder_button)
        row1.addWidget(self.random_folder_button)

        # Row 2: Sort combo, stretch, enqueue button
        row2 = QHBoxLayout()
        row2.addWidget(self.sort_combo)
        row2.addStretch()
        row2.addWidget(self.enqueue_playlist_button)

        main_layout.addLayout(row1)
        main_layout.addLayout(row2)

    def _create_enqueue_playlist_button(self) -> ActionButton:
        button = ActionButton(
            self,
            icon_name="fa6s.list-ordered",
            tooltip=self.lang.ui.folder_list.enqueue_playlist,
        )
        button.setFixedSize(30, 30)
        button.clicked.connect(self.enqueue_playlist_requested)
        return button

    def _create_clear_filter_button(self) -> ActionButton:
        button = ActionButton(
            self,
            icon_name="fa6s.filter-circle-xmark",
            tooltip=self.lang.ui.folder_list.clear_filter_and_search,
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
            button.setToolTip(self.lang.ui.folder_list.previous_folder)
            button.clicked.connect(self.backward_clicked)
        elif direction == "forward":
            button.set_action_icon("fa6s.share")
            button.setToolTip(self.lang.ui.folder_list.next_folder)
            button.clicked.connect(self.forward_clicked)
        elif direction == "random":
            button.set_action_icon("fa6s.dice")
            button.setToolTip(self.lang.ui.folder_list.random_folder)
            button.clicked.connect(self.random_clicked)

        return button

    def _create_sort_combo(self) -> QComboBox:
        combo = SelectComboBox(self)
        combo.setObjectName("folderListSortCombo")
        model = self._sort_model
        combo.setModel(model)

        model.appendRow(
            self._sort_item(self.lang.ui.folder_list.sort_default, "default")
        )
        model.appendRow(
            self._sort_item(self.lang.ui.folder_list.sort_filter, "filter_sort")
        )

        other_heading = QStandardItem(self.lang.ui.folder_list.sort_other)
        other_heading.setFlags(Qt.ItemFlag.NoItemFlags)
        model.appendRow(other_heading)
        for label, value in (
            (self.lang.ui.folder_list.sort_a_z, "a_z"),
            (self.lang.ui.folder_list.sort_z_a, "z_a"),
            (self.lang.ui.folder_list.sort_last_played, "last_played"),
            (self.lang.ui.folder_list.sort_qty_played, "qty_played"),
        ):
            model.appendRow(self._sort_item(label, value))

        combo.setToolTip(self.lang.ui.folder_list.sort_folders)
        combo.setFixedWidth(220)
        combo.currentIndexChanged.connect(self._on_sort_changed)
        return combo

    @staticmethod
    def _sort_item(label: str, value: str) -> QStandardItem:
        item = QStandardItem(label)
        item.setData(value, Qt.ItemDataRole.UserRole)
        return item

    def _on_sort_changed(self, index: int) -> None:
        item = self._sort_model.item(index)
        if item is not None and item.flags() != Qt.ItemFlag.NoItemFlags:
            value = item.data(Qt.ItemDataRole.UserRole)
            if value:
                self.sort_changed.emit(str(value))

    def set_filter_sort_label(self, label: str) -> None:
        item = self._sort_model.item(1)
        if item is not None:
            item.setText(
                self.lang.ui.folder_list.sort_filter_with_label.format(label=label)
            )

    def apply_theme(self):
        self.title_label.setStyleSheet(APP_THEME.label_qss())
        self.help_icon.setStyleSheet(APP_THEME.help_icon_label_qss())
