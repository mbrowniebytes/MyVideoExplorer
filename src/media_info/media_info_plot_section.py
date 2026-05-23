from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QSizePolicy,
)
from src.theme.theme import APP_THEME


class MediaInfoPlotSection(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_plot = ""
        self.setObjectName("section_plot")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.layout.setSpacing(0)

        self.plot_label = QLabel("P\nl\no\nt")
        self.plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plot_label.setWordWrap(False)
        self.plot_label.setStyleSheet(APP_THEME.secondary_label_qss())
        self.plot_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding
        )

        self.plot_text = QPlainTextEdit()
        self.plot_text.setReadOnly(True)
        self.plot_text.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.plot_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.plot_text.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.label_layout = QHBoxLayout()
        self.label_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.label_layout.addWidget(self.plot_label)
        self.label_layout.addWidget(self.plot_text)
        self.layout.addLayout(self.label_layout)

    def build(self, plot: str) -> None:
        if hasattr(self, "_current_plot") and self._current_plot == plot:
            return
        self._current_plot = plot
        self.plot_text.setPlainText(plot)
        self.apply_theme()

    def get_plot_text(self) -> QPlainTextEdit:
        return self.plot_text

    def apply_theme(self) -> None:
        font = QFont(APP_THEME.font_family, APP_THEME.font_size - 5)
        self.plot_text.setFont(font)
        self.plot_text.document().setDefaultFont(font)

        plot_content = self.plot_text.toPlainText()
        self.plot_text.setMaximumHeight(
            self._plot_max_height(self.plot_text, plot_content)
        )

    def _plot_max_height(self, plot_text: QPlainTextEdit, plot: str) -> int:
        if not plot:
            return 50
        fuzzy_len = len(plot) / 60
        max_height = fuzzy_len * plot_text.fontMetrics().lineSpacing() * 1.2
        if max_height > 150:
            return 150
        if max_height < 60:
            return 60
        return int(max_height)
