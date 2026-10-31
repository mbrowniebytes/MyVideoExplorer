from __future__ import annotations

from random import choice
from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QWidget,
)

from MyVideoExplorer.theme.theme import APP_THEME

if TYPE_CHECKING:
    from MyVideoExplorer.folder_filter.folder_filter_table import FolderFilterTable


# Preset definitions: (display_text, tooltip, value_key)
_QTY_PLAYED_PRESETS = [
    ("Never", "Never played (0 times)", "0"),
    ("Once", "Played exactly 1 time", "1"),
    ("Twice", "Played exactly 2 times", "2"),
    ("Thrice", "Played exactly 3 times", "3"),
    ("Handful", "Played exactly 5 times", "5"),
    ("< Dozen", "Played fewer than 12 times", "<12"),
    ("< 50", "Played fewer than 50 times", "<50"),
    ("< 100", "Played fewer than 100 times", "<100"),
    ("> 100", "Played more than 100 times", ">100"),
    ("Custom", "Specify a custom quantity comparison", "custom"),
]


class FilterQtyPlayedWidget(QWidget):
    """
    Inline widget for the 'Qty Played' META filter.

    Provides preset quantity ranges (never, once, twice, etc.) and a custom
    mode with a comparison operator (<, >, =) and a number spinner.
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
        self._op_combo: QComboBox | None = None
        self._spin_box: QSpinBox | None = None
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
        for preset_text, tooltip, _key in _QTY_PLAYED_PRESETS:
            self._preset_combo.addItem(preset_text)
            idx = self._preset_combo.count() - 1
            self._preset_combo.setItemData(idx, tooltip, Qt.ItemDataRole.ToolTipRole)
        APP_THEME.setup_combo_box(self._preset_combo)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        layout.addWidget(self._preset_combo, 1)

        # Custom controls (hidden by default)
        custom_layout = QHBoxLayout()
        custom_layout.setSpacing(4)

        self._op_combo = QComboBox(self)
        self._op_combo.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 6))
        for operator, tooltip in (
            ("<", "Less than the specified number"),
            (">", "Greater than the specified number"),
            ("=", "Exactly the specified number"),
            ("<=", "Less than or equal to the specified number"),
            (">=", "Greater than or equal to the specified number"),
            ("!=", "Not equal to the specified number"),
        ):
            self._op_combo.addItem(operator)
            self._op_combo.setItemData(
                self._op_combo.count() - 1, tooltip, Qt.ItemDataRole.ToolTipRole
            )
        APP_THEME.setup_combo_box(self._op_combo)
        self._op_combo.setVisible(False)
        custom_layout.addWidget(self._op_combo)

        self._spin_box = QSpinBox(self)
        self._spin_box.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 6))
        self._spin_box.setMinimum(0)
        self._spin_box.setMaximum(9999)
        self._spin_box.setValue(1)
        self._spin_box.setToolTip("Number of times played")
        self._spin_box.setVisible(False)
        custom_layout.addWidget(self._spin_box, 1)

        layout.addLayout(custom_layout, 0)

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
        is_custom = idx == len(_QTY_PLAYED_PRESETS) - 1  # "Custom" is last
        if self._op_combo is not None:
            self._op_combo.setVisible(is_custom)
        if self._spin_box is not None:
            self._spin_box.setVisible(is_custom)
        if is_custom and not self.readonly and self._spin_box is not None:
            self._spin_box.setFocus()

    def _on_random(self) -> None:
        """Randomly select a preset or randomize custom values."""
        if self._preset_combo is None:
            return

        # 50% chance to pick a preset (excluding custom), 50% to pick custom
        if choice([True, False]):
            # Pick a random preset (not custom)
            preset_count = len(_QTY_PLAYED_PRESETS) - 1
            if preset_count > 0:
                rand_idx = choice(range(preset_count))
                self._preset_combo.setCurrentIndex(rand_idx)
        else:
            # Pick custom and randomize its values
            self._preset_combo.setCurrentIndex(len(_QTY_PLAYED_PRESETS) - 1)
            if self._op_combo is not None:
                self._op_combo.setCurrentIndex(choice(range(self._op_combo.count())))
            if self._spin_box is not None:
                self._spin_box.setValue(choice(range(201)))

    def get_value(self) -> str:
        """
        Serialize the current filter value.

        Returns a string in the format:
        - For presets: the preset key (e.g., "0", "1", "<12", ">100")
        - For custom: "custom|<op>|<number>" (e.g., "custom|>|50")
        """
        if self._preset_combo is None:
            return ""
        idx = self._preset_combo.currentIndex()
        if idx < 0 or idx >= len(_QTY_PLAYED_PRESETS):
            return ""
        _, _, key = _QTY_PLAYED_PRESETS[idx]
        if key != "custom":
            return key
        # Custom mode
        op = self._op_combo.currentText() if self._op_combo is not None else ">"
        val = self._spin_box.value() if self._spin_box is not None else 0
        return f"custom|{op}|{val}"

    def set_value(self, value: str) -> None:
        """Restore a serialized filter value."""
        if not value:
            return

        if value.startswith("custom|"):
            # Parse custom value
            parts = value.split("|")
            if len(parts) >= 3:
                _prefix, op, num_str = parts[0], parts[1], parts[2]
                if self._preset_combo is not None:
                    self._preset_combo.setCurrentIndex(len(_QTY_PLAYED_PRESETS) - 1)
                if self._op_combo is not None:
                    idx = self._op_combo.findText(op)
                    if idx >= 0:
                        self._op_combo.setCurrentIndex(idx)
                if self._spin_box is not None:
                    try:
                        self._spin_box.setValue(int(num_str))
                    except ValueError:
                        pass
            return

        # Preset value
        if self._preset_combo is not None:
            for i, (_, _, key) in enumerate(_QTY_PLAYED_PRESETS):
                if key == value:
                    self._preset_combo.setCurrentIndex(i)
                    return

    def apply_theme(self) -> None:
        APP_THEME.refresh_theme(self)
        if self._preset_combo is not None:
            APP_THEME.setup_combo_box(self._preset_combo)
        if self._op_combo is not None:
            APP_THEME.setup_combo_box(self._op_combo)
