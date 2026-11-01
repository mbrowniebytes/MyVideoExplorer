from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

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
        layout.addStretch(1)

    def apply_theme(self) -> None:
        super().apply_theme()
        self.setStyleSheet(APP_THEME.container_qss())
