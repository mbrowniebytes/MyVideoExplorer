from __future__ import annotations

from PySide6.QtCore import QDate, QEvent, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QMenu,
    QSpinBox,
    QStyle,
    QStyleOptionSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.db.db_tags import DbTags
from MyVideoExplorer.media_info_side.media_info_side_facts_widget import (
    MediaInfoSideFactsWidget,
)
from MyVideoExplorer.media_info_side.media_info_side_header_widget import (
    MediaInfoSideHeaderWidget,
)
from MyVideoExplorer.tag_cloud.tag_cloud_media import TagCloudMedia, TagStateProtocol
from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.str_util import StrUtil


class LastPlayedDateEdit(QDateEdit):
    """Date edit that opens on its selected date, or today when unset."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.calendarWidget().installEventFilter(self)
        self.setToolTip("Press Delete or right-click to clear the date.")

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.calendarWidget() and event.type() == QEvent.Type.Show:
            QTimer.singleShot(0, self._set_calendar_popup_date)
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.setDate(self.minimumDate())
            return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        clear_action = menu.addAction("Clear date")
        if menu.exec(event.globalPos()) == clear_action:
            self.setDate(self.minimumDate())

    def _set_calendar_popup_date(self) -> None:
        calendar = self.calendarWidget()
        popup_date = (
            self.date() if self.date() > self.minimumDate() else QDate.currentDate()
        )
        calendar.blockSignals(True)
        calendar.setSelectedDate(popup_date)
        calendar.setCurrentPage(popup_date.year(), popup_date.month())
        calendar.blockSignals(False)


class MediaInfoSideContentWidget(QWidget, ThemableMixin):
    """Reusable framed side panel content for media metadata and quick actions."""

    column_widths_changed = Signal(int)
    played_count_changed = Signal(int)
    last_played_changed = Signal(object)

    def __init__(
        self,
        str_util: StrUtil,
        log_util: LogUtil | None = None,
        parent: QWidget | None = None,
        tag_state: TagStateProtocol | None = None,
        tag_store: DbTags | None = None,
    ) -> None:
        super().__init__(parent)
        self.log_util = log_util or LogUtil()

        self.setObjectName("side_media_info")

        self.header_widget = MediaInfoSideHeaderWidget()
        self.facts_widget = MediaInfoSideFactsWidget(str_util)

        self.content_layout = QHBoxLayout(self)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)

        self.meta_widget = QWidget(self)
        self.meta_layout = QVBoxLayout(self.meta_widget)
        self.meta_layout.setContentsMargins(0, 0, 0, 0)
        self.meta_layout.setSpacing(4)

        self.meta_header_widget = QWidget(self.meta_widget)
        self.meta_header_layout = QHBoxLayout(self.meta_header_widget)
        self.meta_header_layout.setContentsMargins(0, 0, 0, 0)
        self.meta_header_layout.setSpacing(4)
        self.meta_title = QLabel("Meta", self.meta_widget)
        self.meta_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.meta_collapse_button = QToolButton(self.meta_header_widget)
        self.meta_collapse_button.setObjectName("meta_column_toggle")
        self.meta_collapse_button.setCheckable(True)
        self.meta_collapse_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.meta_collapse_button.setAutoRaise(True)
        self.meta_collapse_button.setToolTip("Collapse Meta column")
        self.meta_collapse_button.setAccessibleName("Collapse Meta column")
        self.meta_collapse_button.setIconSize(QSize(16, 16))
        self.meta_collapse_button.setFixedSize(40, 28)
        self._update_meta_collapse_button(False)
        self.meta_header_layout.addStretch()
        self.meta_header_layout.addWidget(self.meta_title)
        self.meta_header_layout.addWidget(self.meta_collapse_button)
        self.meta_header_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.meta_body_widget = QWidget(self.meta_widget)
        self.meta_body_layout = QVBoxLayout(self.meta_body_widget)
        self.meta_body_layout.setContentsMargins(0, 0, 0, 0)
        self.meta_body_layout.setSpacing(4)
        self.played_label = QLabel("Played", self.meta_widget)
        self.played_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.played_spin_box = QSpinBox(self.meta_widget)
        self.played_spin_box.setMinimum(0)
        self.played_spin_box.setMaximum(2_147_483_647)
        self.played_spin_box.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin_style = self.played_spin_box.style()
        spin_option = QStyleOptionSpinBox()
        spin_option.initFrom(self.played_spin_box)
        spinner_width = spin_style.subControlRect(
            QStyle.ComplexControl.CC_SpinBox,
            spin_option,
            QStyle.SubControl.SC_SpinBoxUp,
            self.played_spin_box,
        ).width()
        spin_frame_width = spin_style.pixelMetric(
            self.played_spin_box.style().PixelMetric.PM_SpinBoxFrameWidth
        )
        spinner_width = max(spinner_width, self.played_spin_box.fontMetrics().height())
        digits_width = QFontMetrics(self.played_spin_box.font()).horizontalAdvance(
            "1234"
        )
        self.played_spin_box.setFixedWidth(
            digits_width + spinner_width + spin_frame_width * 2 + 44
        )
        self.last_played_label = QLabel("Last Played", self.meta_widget)
        self.last_played_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.last_played_date_edit = LastPlayedDateEdit(self.meta_widget)
        self.last_played_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.last_played_date_edit.setMinimumDate(QDate(1900, 1, 1))
        self.last_played_date_edit.setSpecialValueText("Never")
        self.last_played_date_edit.setDate(self.last_played_date_edit.minimumDate())
        date_text_width = self.last_played_date_edit.fontMetrics().horizontalAdvance(
            "0000-00-00"
        )
        self.last_played_date_edit.setFixedWidth(date_text_width + 44)
        self.tag_cloud_widget = TagCloudMedia(tag_state, tag_store, self.meta_widget)
        self.meta_body_layout.addWidget(self.played_label)
        self.meta_body_layout.addWidget(
            self.played_spin_box, 0, Qt.AlignmentFlag.AlignRight
        )
        self.meta_body_layout.addWidget(self.last_played_label)
        self.meta_body_layout.addWidget(self.last_played_date_edit)
        self.meta_body_layout.addWidget(self.tag_cloud_widget)
        self.meta_body_layout.addStretch()
        self.meta_layout.addWidget(self.meta_header_widget)
        self.meta_layout.addWidget(self.meta_body_widget)

        self.nfo_widget = QWidget(self)
        self.nfo_layout = QVBoxLayout(self.nfo_widget)
        self.nfo_layout.setContentsMargins(0, 0, 0, 0)
        self.nfo_layout.setSpacing(0)
        self.nfo_layout.addWidget(self.header_widget)
        self.nfo_body_widget = QWidget(self.nfo_widget)
        self.nfo_body_layout = QVBoxLayout(self.nfo_body_widget)
        self.nfo_body_layout.setContentsMargins(0, 0, 0, 0)
        self.nfo_body_layout.setSpacing(0)
        self.nfo_body_layout.addWidget(self.facts_widget)
        self.nfo_layout.addWidget(self.nfo_body_widget)

        self._meta_expanded_width = self.last_played_date_edit.width()
        self._nfo_expanded_width = 300 - self._meta_expanded_width - 8
        self.meta_widget.setFixedWidth(self._meta_expanded_width)
        self.nfo_widget.setFixedWidth(self._nfo_expanded_width)
        self.content_layout.addWidget(self.meta_widget, 0)
        self.content_layout.addWidget(self.nfo_widget, 1)

        self._nfo_available = True
        self.meta_collapse_button.toggled.connect(self._set_meta_collapsed)
        self.header_widget.collapse_toggled.connect(self._set_nfo_collapsed)
        self.played_spin_box.valueChanged.connect(self.played_count_changed)
        self.last_played_date_edit.dateChanged.connect(
            lambda played_date: self.last_played_changed.emit(played_date)
        )

        self.apply_theme()

    def update_from_movie_info(self, movie_info: dict) -> None:
        self.facts_widget.update_from_movie_info(movie_info)

    def set_nfo_available(self, available: bool) -> None:
        self._nfo_available = available
        self.nfo_body_widget.setVisible(
            available and not self.header_widget.collapse_button.isChecked()
        )

    def apply_theme(self) -> None:
        self._resize_meta_column()
        self._resize_played_counter()
        if not APP_THEME.is_refreshing:
            super().apply_theme()
            return

        self.setStyleSheet(APP_THEME.container_qss())
        for label in (self.meta_title, self.played_label, self.last_played_label):
            label.setStyleSheet(APP_THEME.secondary_label_qss())
        self.meta_collapse_button.setStyleSheet(
            APP_THEME.toggle_button_qss(self.meta_collapse_button.objectName())
        )
        self.header_widget.apply_theme()
        self.facts_widget.apply_theme()

    def _resize_meta_column(self) -> None:
        date_text_width = self.last_played_date_edit.fontMetrics().horizontalAdvance(
            "0000-00-00"
        )
        date_edit_width = date_text_width + 44
        self.last_played_date_edit.setFixedWidth(date_edit_width)
        self._meta_expanded_width = date_edit_width
        if hasattr(self, "_nfo_expanded_width"):
            self._nfo_expanded_width = max(0, 300 - date_edit_width - 8)
        if not self.meta_collapse_button.isChecked():
            self._set_column_widths()

    def _resize_played_counter(self) -> None:
        digits_width = self.played_spin_box.fontMetrics().horizontalAdvance("1234")
        spinner_width = self.played_spin_box.fontMetrics().height()
        frame_width = self.played_spin_box.style().pixelMetric(
            QStyle.PixelMetric.PM_SpinBoxFrameWidth
        )
        self.played_spin_box.setFixedWidth(
            digits_width + spinner_width + frame_width * 2 + 44
        )

    def _set_meta_collapsed(self, collapsed: bool) -> None:
        self.meta_body_widget.setVisible(not collapsed)
        self.meta_title.setVisible(not collapsed)
        label = "Expand" if collapsed else "Collapse"
        self._update_meta_collapse_button(collapsed)
        self.meta_collapse_button.setToolTip(f"{label} Meta column")
        self.meta_collapse_button.setAccessibleName(f"{label} Meta column")
        self._set_column_widths()

    def _update_meta_collapse_button(self, collapsed: bool) -> None:
        icon_name = "fa6s.chevron-down" if collapsed else "fa6s.chevron-up"
        self.meta_collapse_button.setIcon(
            APP_THEME.icon(icon_name, color=APP_THEME.text_color)
        )
        self.meta_collapse_button.setText("M" if collapsed else "")
        self.meta_collapse_button.setFixedSize(40, 28)

    def _set_nfo_collapsed(self, collapsed: bool) -> None:
        self.nfo_body_widget.setVisible(self._nfo_available and not collapsed)
        self._set_column_widths()

    def _set_column_widths(self) -> None:
        meta_width = (
            self.meta_collapse_button.width()
            if self.meta_collapse_button.isChecked()
            else self._meta_expanded_width
        )
        nfo_width = (
            self.header_widget.collapse_button.width()
            if self.header_widget.collapse_button.isChecked()
            else self._nfo_expanded_width
        )
        self.meta_widget.setFixedWidth(meta_width)
        self.nfo_widget.setFixedWidth(nfo_width)
        self.column_widths_changed.emit(meta_width + nfo_width + 8)
