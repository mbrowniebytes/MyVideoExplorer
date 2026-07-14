from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil

PLOT_SECTION_OBJECT_NAME = "section_plot"
PLOT_SECTION_TITLE_TEXT = "P\nl\no\nt"

PLOT_SECTION_MINIMUM_EMPTY_HEIGHT = 50
PLOT_SECTION_MINIMUM_CONTENT_HEIGHT = 60
PLOT_SECTION_MAXIMUM_CONTENT_HEIGHT = 150
PLOT_SECTION_APPROXIMATE_CHARACTERS_PER_LINE = 60
PLOT_SECTION_LINE_HEIGHT_MULTIPLIER = 1.2


class MediaInfoPlotSection(QWidget, ThemableMixin):
    def __init__(self, log_util: LogUtil | None = None, parent=None):
        super().__init__(parent)
        self.log_util = log_util or LogUtil()

        self._current_plot_text = ""

        self.plot_section_layout = QVBoxLayout(self)
        self.plot_content_layout = QHBoxLayout()

        self.plot_title_label = QLabel(PLOT_SECTION_TITLE_TEXT)
        self.plot_text_edit = QPlainTextEdit()

        self._configure_section_frame()
        self._configure_section_layout()
        self._configure_plot_title_label()
        self._configure_plot_text_edit()
        self._build_plot_content_layout()

    def build(self, plot_text: str) -> None:
        if self._current_plot_text == plot_text:
            return

        self._current_plot_text = plot_text
        self.plot_text_edit.setPlainText(plot_text)
        self.apply_theme()

    def get_plot_text(self) -> QPlainTextEdit:
        return self.plot_text_edit

    def apply_theme(self) -> None:
        if not APP_THEME.is_refreshing:
            super().apply_theme()
            return

        font = QFont(APP_THEME.font_family, APP_THEME.font_size - 1)
        font.setPixelSize(APP_THEME.font_size - 1)

        self.plot_text_edit.setFont(font)
        self.plot_text_edit.document().setDefaultFont(font)

        current_plot_text = self.plot_text_edit.toPlainText()
        maximum_plot_text_height = self._calculate_plot_text_maximum_height(
            plot_text_edit=self.plot_text_edit,
            plot_text=current_plot_text,
        )
        self.plot_text_edit.setMaximumHeight(maximum_plot_text_height)

    def _configure_section_frame(self) -> None:
        self.setObjectName(PLOT_SECTION_OBJECT_NAME)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def _configure_section_layout(self) -> None:
        self.plot_section_layout.setContentsMargins(0, 5, 0, 5)
        self.plot_section_layout.setSpacing(0)

    def _configure_plot_title_label(self) -> None:
        self.plot_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plot_title_label.setWordWrap(False)
        self.plot_title_label.setStyleSheet(APP_THEME.secondary_label_qss())
        self.plot_title_label.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.MinimumExpanding,
        )

    def _configure_plot_text_edit(self) -> None:
        self.plot_text_edit.setReadOnly(True)
        self.plot_text_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.plot_text_edit.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )
        self.plot_text_edit.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )

    def _build_plot_content_layout(self) -> None:
        self.plot_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.plot_content_layout.addWidget(self.plot_title_label)
        self.plot_content_layout.addWidget(self.plot_text_edit)

        self.plot_section_layout.addLayout(self.plot_content_layout)

    def _calculate_plot_text_maximum_height(
        self,
        plot_text_edit: QPlainTextEdit,
        plot_text: str,
    ) -> int:
        if not plot_text:
            return PLOT_SECTION_MINIMUM_EMPTY_HEIGHT

        estimated_line_count = (
            len(plot_text) / PLOT_SECTION_APPROXIMATE_CHARACTERS_PER_LINE
        )
        estimated_content_height = (
            estimated_line_count
            * plot_text_edit.fontMetrics().lineSpacing()
            * PLOT_SECTION_LINE_HEIGHT_MULTIPLIER
        )

        if estimated_content_height > PLOT_SECTION_MAXIMUM_CONTENT_HEIGHT:
            return PLOT_SECTION_MAXIMUM_CONTENT_HEIGHT

        if estimated_content_height < PLOT_SECTION_MINIMUM_CONTENT_HEIGHT:
            return PLOT_SECTION_MINIMUM_CONTENT_HEIGHT

        return int(estimated_content_height)
