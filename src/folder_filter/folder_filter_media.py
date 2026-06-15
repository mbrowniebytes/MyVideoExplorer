from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from src.theme.theme import APP_THEME
from src.settings.settings import Settings


class FolderFilterMedia(QWidget):
    sig_apply_filters = Signal()

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.media_button_group: list[QPushButton] = []
        self.media_layout = QHBoxLayout(self)
        self.media_layout.setContentsMargins(0, 0, 0, 0)

        self.all_none_button = QPushButton("")
        self.all_none_button.setCheckable(True)
        self.all_none_button.setChecked(False)
        self.all_none_button.setMinimumHeight(32)
        self.all_none_button.setFixedWidth(32)
        self.all_none_button.setStyleSheet(APP_THEME.small_button_qss())
        self.all_none_button.clicked.connect(self._toggle_all_media_clicked)
        self.media_layout.addWidget(self.all_none_button)

        self._build_buttons()
        self.settings.settings_data_model.sig_settings_changed.connect(self.refresh_buttons)

    def _build_buttons(self) -> None:
        # Map labels to their associated paths and icons (handle multiple paths per label)

        # Group configs by label, storing path->icon mapping
        label_to_info: dict[str, list[tuple[str, str]]] = (
            {}
        )  # label -> [(path, icon_name), ...]

        for config in self.settings.settings_data_model.folder_configs:
            label = config.get("label", "")
            path = config.get("path", "")
            if not path:
                continue

            icon_name = config.get("icon", "fa5s.folder")

            if not label:
                continue

            if label not in label_to_info:
                label_to_info[label] = []
            label_to_info[label].append((path, icon_name))

        # Sort labels
        for label in sorted(label_to_info.keys()):
            info_list = label_to_info[label]

            abbrev = label[:4]

            # Get the icon pixmap for this button
            # For icons: take the first valid icon name found for this label's paths
            display_icon_name = None
            for p, icon_name in info_list:
                try:
                    qicon = APP_THEME.icon(icon_name)
                    if qicon:
                        display_icon_name = icon_name
                        break
                except Exception:
                    continue

            if not display_icon_name and info_list:
                # Default to folder icon if no valid icon found
                display_icon_name = "fa5s.folder"

            qicon = APP_THEME.icon(display_icon_name)
            if qicon:
                icon_pixmap = qicon.pixmap(18, 18)
            else:
                icon_pixmap = None

            btn = QPushButton(abbrev)
            btn.setToolTip(label)
            btn.setCheckable(True)
            btn.setMinimumHeight(32)
            btn.setIcon(icon_pixmap)
            btn.setStyleSheet(APP_THEME.small_button_qss())

            # Collect all paths for this label (filter out duplicates if same path appears multiple times)
            unique_paths = list(
                dict.fromkeys(p for p, _ in info_list)
            )  # keep order, remove dupes

            btn.setProperty("media_paths", unique_paths)

            # Signal emission is handled by parent or via a local signal
            btn.clicked.connect(self._on_button_clicked)
            self.media_layout.addWidget(btn)
            self.media_button_group.append(btn)

    def _on_button_clicked(self) -> None:
        # Update "All/None" text if needed and notify
        # self._update_all_none_text()
        self.sig_apply_filters.emit()

    def _toggle_all_media_clicked(self) -> None:
        any_unchecked = any(not btn.isChecked() for btn in self.media_button_group)
        new_state = any_unchecked
        for btn in self.media_button_group:
            btn.setChecked(new_state)

        # self._update_all_none_text()
        self.sig_apply_filters.emit()

    def _update_all_none_text(self) -> None:
        any_unchecked = any(not btn.isChecked() for btn in self.media_button_group)
        if any_unchecked:
            self.all_none_button.setText("All")
        else:
            self.all_none_button.setText("None")

    def refresh_buttons(self) -> None:
        # Clear existing
        for i in reversed(range(self.media_layout.count())):
            item = self.media_layout.itemAt(i)
            if item and item.widget() and item.widget() != self.all_none_button:
                item.widget().setParent(None)

        # Remove stretch if it exists
        for i in reversed(range(self.media_layout.count())):
            item = self.media_layout.itemAt(i)
            if item.spacerItem():
                self.media_layout.removeItem(item)

        self.media_button_group = []
        self._build_buttons()

    def collect_filters(self) -> list[dict]:
        filters = []
        for btn in self.media_button_group:
            if btn.isChecked():
                paths = btn.property("media_paths")
                if paths:
                    filters.append({"filter": "media", "value": paths})
        return filters
