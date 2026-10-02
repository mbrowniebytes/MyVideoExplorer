from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from MyVideoExplorer.db.db_tags import DbTags
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.tag_cloud.tag_cloud_widget import TagCloudWidget


class TagCloudSettings(QWidget):
    def __init__(
        self,
        state: SettingsState,
        tag_store: DbTags | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.tag_store = tag_store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.cloud = TagCloudWidget(editable=True, deletable=True, parent=self)
        layout.addWidget(self.cloud)

        self.cloud.tag_edited.connect(self._on_tag_edited)
        self.cloud.tag_color_changed.connect(self._on_tag_color_changed)
        self.cloud.tag_deleted.connect(self._on_tag_deleted)
        self.state.tags_changed.connect(self.refresh)
        self.state.tag_counts_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        source_tags = self.tag_store.list_tags() if self.tag_store else self.state.tags
        counts = self.tag_store.get_tag_counts() if self.tag_store else {}
        self.cloud.set_tags(
            [
                {
                    **tag,
                    "qty": counts.get(tag["tag"].casefold(), 0),
                }
                for tag in source_tags
            ]
        )

    def _on_tag_edited(self, old_name: str, new_tag: dict) -> None:
        if self.tag_store is not None:
            if not self.tag_store.update_catalog_tag(
                old_name, new_tag["tag"], new_tag["color"]
            ):
                self.refresh()
            return
        self.state.set_tags(
            [
                new_tag if tag["tag"].casefold() == old_name.casefold() else tag
                for tag in self.state.tags
            ]
        )

    def _on_tag_color_changed(self, tag_name: str, color: str) -> None:
        if self.tag_store is not None:
            if not self.tag_store.set_tag_color(tag_name, color):
                self.refresh()
            return
        self.state.set_tags(
            [
                {**tag, "color": color}
                if tag["tag"].casefold() == tag_name.casefold()
                else tag
                for tag in self.state.tags
            ]
        )

    def _on_tag_deleted(self, tag_name: str) -> None:
        if self.tag_store is not None:
            if not self.tag_store.delete_catalog_tag(tag_name):
                self.refresh()
            return
        self.state.set_tags(
            [
                tag
                for tag in self.state.tags
                if tag["tag"].casefold() != tag_name.casefold()
            ]
        )
