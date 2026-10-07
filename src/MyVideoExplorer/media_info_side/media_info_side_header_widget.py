from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil


class MediaInfoSideHeaderWidget(QWidget, ThemableMixin):
    """Compact label identifying the NFO metadata column."""

    collapse_toggled = Signal(bool)

    def __init__(
        self, log_util: LogUtil | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.log_util = log_util or LogUtil()

        self.header_layout = QHBoxLayout(self)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(4)

        self.title_label = QLabel("NFO", parent=self)
        self.title_label.setWordWrap(False)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.collapse_button = QToolButton(self)
        self.collapse_button.setObjectName("nfo_column_toggle")
        self.collapse_button.setCheckable(True)
        self.collapse_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.collapse_button.setAutoRaise(True)
        self.collapse_button.setToolTip("Collapse NFO column")
        self.collapse_button.setAccessibleName("Collapse NFO column")
        self.collapse_button.setIconSize(QSize(16, 16))
        self.collapse_button.setFixedSize(40, 28)
        self._update_collapse_button(False)
        self.collapse_button.toggled.connect(self._update_collapse_button)
        self.collapse_button.toggled.connect(self.collapse_toggled)

        self.header_layout.addWidget(self.title_label)
        self.header_layout.addWidget(self.collapse_button)
        self.header_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.apply_theme()

    def apply_theme(self) -> None:
        if not APP_THEME.is_refreshing:
            super().apply_theme()
            return

        self.title_label.setStyleSheet(APP_THEME.secondary_label_qss())
        self.collapse_button.setStyleSheet(
            APP_THEME.toggle_button_qss(self.collapse_button.objectName())
        )

    def _update_collapse_button(self, collapsed: bool) -> None:
        label = "Expand" if collapsed else "Collapse"
        self.title_label.setVisible(not collapsed)
        icon_name = "fa6s.chevron-down" if collapsed else "fa6s.chevron-up"
        self.collapse_button.setIcon(
            APP_THEME.icon(icon_name, color=APP_THEME.text_color)
        )
        self.collapse_button.setText("I" if collapsed else "")
        self.collapse_button.setFixedSize(40, 28)
        self.collapse_button.setToolTip(f"{label} NFO column")
        self.collapse_button.setAccessibleName(f"{label} NFO column")
