from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.db.db_tags import DbTags
from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.tag_cloud.tag_cloud_settings import TagCloudSettings
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil


class SettingsTagsTab(SettingsBaseTab):
    def __init__(
        self,
        state: SettingsState,
        log_util: LogUtil,
        tag_store: DbTags | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(log_util, parent)
        self.state = state
        self.tag_store = tag_store
        self.tag_cloud_settings = TagCloudSettings(state, tag_store, self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tag_cloud_settings)

        add_row = QHBoxLayout()
        self.new_tag_edit = QLineEdit(self)
        self.new_tag_edit.setPlaceholderText("New tag name")
        self.add_tag_button = QPushButton("Add Tag", self)
        self.add_tag_button.clicked.connect(self._add_tag)
        self.new_tag_edit.returnPressed.connect(self._add_tag)
        add_row.addWidget(self.new_tag_edit, 1)
        add_row.addWidget(self.add_tag_button)
        layout.addLayout(add_row)
        layout.addStretch(1)

    def _add_tag(self) -> None:
        tag = self.new_tag_edit.text().strip()
        if not tag:
            return
        if not self.state.is_valid_tag_name(tag):
            self.new_tag_edit.setToolTip("Tag names must be alphanumeric only.")
            return
        if self.tag_store is not None:
            added = self.tag_store.add_catalog_tag(tag)
        else:
            added = self.state.add_tag(tag)
        if not added:
            self.new_tag_edit.setToolTip("A tag with this name already exists.")
            return
        self.new_tag_edit.clear()
        self.tag_cloud_settings.refresh()

    def apply_theme(self) -> None:
        super().apply_theme()
        self.setStyleSheet(APP_THEME.container_qss())
