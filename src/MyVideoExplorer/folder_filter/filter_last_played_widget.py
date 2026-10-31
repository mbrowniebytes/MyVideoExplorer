from __future__ import annotations

from datetime import UTC, datetime, timedelta
from random import choice
from typing import TYPE_CHECKING

from PySide6.QtCore import QDate, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from MyVideoExplorer.theme.theme import APP_THEME

if TYPE_CHECKING:
    from MyVideoExplorer.folder_filter.folder_filter_table import FolderFilterTable


# Preset definitions: (display_text, tooltip, value_key)
# value_key is used to serialize the selection
_LAST_PLAYED_PRESETS = [
    ("Never", "Files that have never been played", "never"),
    ("Yesterday", "Last played yesterday", "yesterday"),
    ("Last Week", "Last played within the last 7 days", "last_week"),
    (
        "Last Month",
        "Last played in the previous calendar month (1st to last day)",
        "last_month",
    ),
    ("Last Year", "Last played in the previous calendar year", "last_year"),
    ("Custom", "Specify a custom date comparison", "custom"),
]


class FilterLastPlayedWidget(QWidget):
    """
    Inline widget for the 'Last Played' META filter.

    Provides preset date ranges (never, yesterday, last week, etc.) and a
    custom mode with a comparison operator (<, >, =) and a date picker.
    A random button randomly selects a preset or randomizes the custom values.
    """

    def __init__(
        self,
        table: FolderFilterTable,
        readonly: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent or table)
        self.table = table
        self.readonly = readonly
        self._preset_combo: QComboBox | None = None
        self._custom_layout: QHBoxLayout | None = None
        self._op_combo: QComboBox | None = None
        self._date_edit: QDateEdit | None = None
        self._random_btn: QToolButton | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = self.layout()
        assert isinstance(layout, QHBoxLayout)

        # Preset combo box
        self._preset_combo = QComboBox(self)
        self._preset_combo.setFont(
            QFont(APP_THEME.font_family, APP_THEME.font_size - 6)
        )
        for preset_text, tooltip, _key in _LAST_PLAYED_PRESETS:
            self._preset_combo.addItem(preset_text)
            idx = self._preset_combo.count() - 1
            self._preset_combo.setItemData(idx, tooltip, Qt.ItemDataRole.ToolTipRole)
        APP_THEME.setup_combo_box(self._preset_combo)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        layout.addWidget(self._preset_combo, 1)

        # Custom controls (hidden by default)
        self._custom_layout = QHBoxLayout()
        self._custom_layout.setSpacing(4)

        self._op_combo = QComboBox(self)
        self._op_combo.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 6))
        for operator, tooltip in (
            ("<", "Before the selected date"),
            (">", "After the selected date"),
            ("=", "Exactly on the selected date"),
            ("<=", "On or before the selected date"),
            (">=", "On or after the selected date"),
            ("!=", "Not on the selected date"),
        ):
            self._op_combo.addItem(operator)
            self._op_combo.setItemData(
                self._op_combo.count() - 1, tooltip, Qt.ItemDataRole.ToolTipRole
            )
        APP_THEME.setup_combo_box(self._op_combo)
        self._op_combo.setVisible(False)
        self._custom_layout.addWidget(self._op_combo)

        self._date_edit = QDateEdit(self)
        self._date_edit.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 6))
        self._date_edit.setCalendarPopup(True)
        _today = datetime.now(UTC).date()
        self._date_edit.setDate(QDate(_today.year, _today.month, _today.day))
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        self._date_edit.setVisible(False)
        self._custom_layout.addWidget(self._date_edit, 1)

        for w in (self._op_combo, self._date_edit):
            layout.addLayout(self._custom_layout, 0)
            break  # only add once

        # Random button
        self._random_btn = QToolButton(self)
        self._random_btn.setIcon(
            APP_THEME.icon("fa6s.dice", color=APP_THEME.text_color)
        )
        self._random_btn.setIconSize(QSize(14, 14))
        self._random_btn.setToolTip("Randomize selection")
        self._random_btn.clicked.connect(self._on_random)
        if self.readonly:
            self._random_btn.setVisible(False)
        layout.addWidget(self._random_btn)

    def _on_preset_changed(self, idx: int) -> None:
        """Show/hide custom controls based on selected preset."""
        is_custom = idx == len(_LAST_PLAYED_PRESETS) - 1  # "Custom" is last
        if self._op_combo is not None:
            self._op_combo.setVisible(is_custom)
        if self._date_edit is not None:
            self._date_edit.setVisible(is_custom)
        if is_custom and not self.readonly and self._date_edit is not None:
            self._date_edit.setFocus()

    def _on_random(self) -> None:
        """Randomly select a preset or randomize custom values."""
        if self._preset_combo is None:
            return

        # 50% chance to pick a preset (excluding custom), 50% to pick custom
        if choice([True, False]):
            # Pick a random preset (not custom)
            preset_count = len(_LAST_PLAYED_PRESETS) - 1
            if preset_count > 0:
                rand_idx = choice(range(preset_count))
                self._preset_combo.setCurrentIndex(rand_idx)
        else:
            # Pick custom and randomize its values
            self._preset_combo.setCurrentIndex(len(_LAST_PLAYED_PRESETS) - 1)
            if self._op_combo is not None:
                self._op_combo.setCurrentIndex(choice(range(self._op_combo.count())))
            if self._date_edit is not None:
                # Random date within ±365 days from today
                offset = choice(range(-365, 366))
                rand_date = datetime.now(UTC).date() + timedelta(days=offset)
                self._date_edit.setDate(
                    QDate(rand_date.year, rand_date.month, rand_date.day)
                )

    def get_value(self) -> str:
        """
        Serialize the current filter value.

        Returns a string in the format:
        - For presets: the preset key (e.g., "never", "yesterday", "last_week")
        - For custom: "custom|<op>|<date>" (e.g., "custom|>|2025-01-15")
        """
        if self._preset_combo is None:
            return ""
        idx = self._preset_combo.currentIndex()
        if idx < 0 or idx >= len(_LAST_PLAYED_PRESETS):
            return ""
        _, _, key = _LAST_PLAYED_PRESETS[idx]
        if key != "custom":
            return key
        # Custom mode
        op = self._op_combo.currentText() if self._op_combo is not None else ">"
        dt = (
            self._date_edit.date().toString("yyyy-MM-dd")
            if self._date_edit is not None
            else datetime.now(UTC).date().isoformat()
        )
        return f"custom|{op}|{dt}"

    def set_value(self, value: str) -> None:
        """Restore a serialized filter value."""
        if not value:
            return

        if value.startswith("custom|"):
            # Parse custom value
            parts = value.split("|")
            if len(parts) >= 3:
                _prefix, op, dt_str = parts[0], parts[1], parts[2]
                if self._preset_combo is not None:
                    self._preset_combo.setCurrentIndex(len(_LAST_PLAYED_PRESETS) - 1)
                if self._op_combo is not None:
                    idx = self._op_combo.findText(op)
                    if idx >= 0:
                        self._op_combo.setCurrentIndex(idx)
                if self._date_edit is not None:
                    try:
                        parsed_date = datetime.fromisoformat(dt_str).date()
                        self._date_edit.setDate(
                            QDate(parsed_date.year, parsed_date.month, parsed_date.day)
                        )
                    except ValueError:
                        pass
            return

        # Preset value
        if self._preset_combo is not None:
            for i, (_, _, key) in enumerate(_LAST_PLAYED_PRESETS):
                if key == value:
                    self._preset_combo.setCurrentIndex(i)
                    return

    def apply_theme(self) -> None:
        APP_THEME.refresh_theme(self)
        if self._preset_combo is not None:
            APP_THEME.setup_combo_box(self._preset_combo)
        if self._op_combo is not None:
            APP_THEME.setup_combo_box(self._op_combo)
