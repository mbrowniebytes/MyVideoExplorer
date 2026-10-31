from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from PySide6.QtCore import QDate, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.folder_list.media_nav_search import (
    DATE_OPERATORS,
    QTY_OPERATORS,
    MediaNavSearchCriteria,
)
from MyVideoExplorer.tag_cloud.tag_button import TagButton
from MyVideoExplorer.tag_cloud.tag_picker_dialog import TagPickerDialog
from MyVideoExplorer.tag_cloud.tag_util import get_contrast_text_color
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.widgets.flow_layout import FlowLayout

_NAME_LABELS = {
    "movie_name": "Movie name",
    "folder_name": "Folder name",
    "file_name": "File name",
}
_PERSON_LABELS = {"actor": "Actor", "director": "Director"}
_YEAR_OPERATORS = {"=": "=", "!=": "!=", ">": ">", ">=": ">=", "<": "<", "<=": "<="}
_UNSET_DATE = QDate(1900, 1, 1)


class _SearchSettingsData(Protocol):
    tags: list[dict[str, str]]


class _SearchTagStore(Protocol):
    def list_tags(self) -> list[dict[str, str]]: ...

    def get_tag_counts(self) -> dict[str, int]: ...


class _SearchSettings(Protocol):
    @property
    def settings_data_model(self) -> _SearchSettingsData: ...

    @property
    def tag_store(self) -> _SearchTagStore | None: ...


class _ChipContainer(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.flow_layout = FlowLayout(self, spacing=4)
        self.flow_layout.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.setVisible(False)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return max(self.flow_layout.heightForWidth(width), 0)

    def sizeHint(self) -> QSize:
        width = max(self.width(), 200)
        return QSize(width, self.heightForWidth(width))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.flow_layout.setGeometry(self.rect())

    def clear(self) -> None:
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            widget = item.widget() if item else None
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def refresh_height(self) -> None:
        self.flow_layout.setGeometry(self.rect())
        self.updateGeometry()
        parent = self.parentWidget()
        if parent is not None:
            parent.updateGeometry()


class MediaNavSearchOptionsDialog(QDialog):
    criteria_changed = Signal()
    tag_remove_requested = Signal(str)
    create_filter_requested = Signal(list)  # list of filter dicts

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("Media Search Options")
        self.setStyleSheet(APP_THEME.container_qss())
        self._selected_tags: list[str] = []
        self._tag_colors: dict[str, str] = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        self.setStyleSheet(
            APP_THEME.container_qss()
            + f"""
            QRadioButton {{
                color: {APP_THEME.text_color};
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {APP_THEME.border_color};
                border-radius: 9px;
                background-color: {APP_THEME.background_color};
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid {APP_THEME.config.color_interaction_selected};
                background-color: {APP_THEME.config.color_interaction_selected};
            }}
            QRadioButton:checked {{
                color: {APP_THEME.config.color_interaction_selected_text};
                font-weight: bold;
            }}
            """
        )

        self.name_radios: dict[str, QRadioButton] = {}
        self.name_group = QButtonGroup(self)
        self.name_group.setExclusive(True)
        name_row = QHBoxLayout()
        for field in ("movie_name", "folder_name", "file_name"):
            label = _NAME_LABELS[field]
            radio = QRadioButton(label, self)
            radio.setObjectName(f"search_name_{field}")
            self.name_radios[field] = radio
            self.name_group.addButton(radio)
            name_row.addWidget(radio)
            radio.toggled.connect(self.criteria_changed)
        layout.addLayout(name_row)
        self.name_radios["movie_name"].setChecked(True)
        self._add_separator(layout)

        self.person_radios: dict[str, QRadioButton] = {}
        self.person_inputs: dict[str, QLineEdit] = {}
        self.person_group = QButtonGroup(self)
        self.person_group.setExclusive(True)
        person_row = QHBoxLayout()
        for field, label in _PERSON_LABELS.items():
            radio = QRadioButton(label, self)
            radio.setObjectName(f"search_person_{field}")
            query = QLineEdit(self)
            query.setObjectName(f"search_{field}_query")
            query.setPlaceholderText(f"Search {label.lower()}")
            self.person_radios[field] = radio
            self.person_inputs[field] = query
            self.person_group.addButton(radio)
            person_row.addWidget(radio)
            person_row.addWidget(query, 1)
            radio.toggled.connect(self.criteria_changed)
            query.textChanged.connect(self.criteria_changed)
        layout.addLayout(person_row)
        self.person_radios["director"].setChecked(True)
        self._add_separator(layout)

        self.year_checkbox = QCheckBox("Year", self)
        self.year_operator = self._make_operator_combo(_YEAR_OPERATORS)
        self.year_combo = QComboBox(self)
        self.year_combo.setObjectName("search_year_combo")
        self.year_combo.addItem("- Any -", userData=None)
        year_values = list(range(QDate.currentDate().year(), 1949, -1)) + list(
            range(1940, 1899, -10)
        )
        for year in year_values:
            self.year_combo.addItem(str(year), userData=year)
        for index in range(self.year_combo.count()):
            self.year_combo.setItemData(
                index,
                Qt.AlignmentFlag.AlignLeft,
                Qt.ItemDataRole.TextAlignmentRole,
            )
        self.year_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        year_label_width = max(
            self.year_combo.fontMetrics().horizontalAdvance(str(year))
            for year in year_values
        )
        any_label_width = self.year_combo.fontMetrics().horizontalAdvance("- Any -")
        self.year_combo.setFixedWidth(max(year_label_width, any_label_width) + 56)
        self.year_checkbox.toggled.connect(self.year_combo.setEnabled)
        self.year_checkbox.toggled.connect(self.year_operator.setEnabled)
        self.year_checkbox.toggled.connect(self.criteria_changed)
        self.year_operator.currentIndexChanged.connect(self.criteria_changed)
        self.year_combo.currentIndexChanged.connect(self.criteria_changed)
        self.year_combo.setEnabled(False)
        self.year_operator.setEnabled(False)
        year_row = QHBoxLayout()
        year_row.addWidget(self.year_checkbox)
        year_row.addWidget(self.year_operator)
        year_row.addWidget(self.year_combo)
        year_row.addStretch(1)
        layout.addLayout(year_row)

        self.qty_checkbox = QCheckBox("Qty Played", self)
        self.qty_operator = self._make_operator_combo(QTY_OPERATORS)
        self.qty_value = QSpinBox(self)
        self.qty_value.setObjectName("search_qty_value")
        self.qty_value.setRange(-1, 2_147_483_647)
        self.qty_value.setSpecialValueText("")
        self.qty_value.setFixedWidth(
            self.qty_value.fontMetrics().horizontalAdvance("00000") + 72
        )
        self.qty_value.lineEdit().setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.qty_checkbox.toggled.connect(self.qty_operator.setEnabled)
        self.qty_checkbox.toggled.connect(self.qty_value.setEnabled)
        self.qty_operator.setEnabled(False)
        self.qty_value.setEnabled(False)
        qty_row = QHBoxLayout()
        qty_row.addWidget(self.qty_checkbox)
        qty_row.addWidget(self.qty_operator)
        qty_row.addWidget(self.qty_value)
        qty_row.addStretch(1)
        layout.addLayout(qty_row)

        self.date_checkbox = QCheckBox("Date Last Played", self)
        self.date_operator = self._make_operator_combo(DATE_OPERATORS)
        self.date_start = self._make_date_edit()
        self.date_checkbox.toggled.connect(self.date_operator.setEnabled)
        self.date_checkbox.toggled.connect(self.date_start.setEnabled)
        self.date_operator.setEnabled(False)
        self.date_start.setEnabled(False)
        date_row = QHBoxLayout()
        date_row.addWidget(self.date_checkbox)
        date_row.addWidget(self.date_operator)
        date_row.addWidget(self.date_start)
        date_row.addStretch(1)
        layout.addLayout(date_row)
        self._add_separator(layout)

        tag_row = QHBoxLayout()
        self.tags_checkbox = QCheckBox("Tags", self)
        self.select_tags_button = self._make_button("Select Tags", "fa6s.tag")
        self.select_tags_button.setEnabled(False)
        self.tags_checkbox.toggled.connect(self.select_tags_button.setEnabled)
        self.tags_checkbox.toggled.connect(self.criteria_changed)
        self.select_tags_button.clicked.connect(self.criteria_changed)
        tag_row.addWidget(self.tags_checkbox)
        tag_row.addStretch(1)
        tag_row.addWidget(self.select_tags_button)
        layout.addLayout(tag_row)
        self.selected_tags_container = _ChipContainer(self)
        layout.addWidget(self.selected_tags_container)

        # Create Filter button at bottom-right
        bottom_row = QHBoxLayout()
        bottom_row.addStretch(1)
        self.create_filter_button = self._make_button(
            "Create Filter from Search", "fa6s.circle-plus"
        )
        self.create_filter_button.clicked.connect(self._on_create_filter)
        bottom_row.addWidget(self.create_filter_button)
        layout.addLayout(bottom_row)

        for checkbox in (self.qty_checkbox, self.date_checkbox):
            checkbox.toggled.connect(self.criteria_changed)
        for control in (
            self.qty_operator,
            self.date_operator,
        ):
            control.currentIndexChanged.connect(self.criteria_changed)
        self.qty_value.valueChanged.connect(self.criteria_changed)
        self.date_start.dateChanged.connect(self.criteria_changed)

    @staticmethod
    def _add_separator(layout: QVBoxLayout) -> None:
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

    def _add_filter_row(
        self,
        layout: QVBoxLayout,
        checkbox: QCheckBox,
        controls: list[QWidget],
    ) -> None:
        row = QHBoxLayout()
        row.addWidget(checkbox)
        row.addStretch(1)
        for control in controls:
            row.addWidget(control)
        layout.addLayout(row)
        for control in controls:
            checkbox.toggled.connect(control.setEnabled)
            control.setEnabled(checkbox.isChecked())

    def _make_operator_combo(self, operators: dict[str, str]) -> QComboBox:
        combo = QComboBox(self)
        combo.addItems(list(operators))
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        combo.setFixedWidth(max(combo.sizeHint().width(), 42))
        return combo

    @staticmethod
    def _make_button(label: str, icon_name: str) -> QToolButton:
        button = QToolButton()
        button.setToolTip(label)
        button.setIcon(APP_THEME.icon(icon_name, color=APP_THEME.text_color))
        button.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
        button.setFixedSize(36, 32)
        return button

    def _make_date_edit(self) -> QDateEdit:
        edit = QDateEdit(self)
        edit.setCalendarPopup(True)
        edit.setMinimumDate(_UNSET_DATE)
        edit.setMaximumDate(QDate.currentDate())
        edit.setDate(QDate.currentDate())
        edit.setDisplayFormat("yyyy-MM-dd")
        edit.setMinimumWidth(edit.fontMetrics().horizontalAdvance("YYYY-MM-DD") + 48)
        edit.lineEdit().setAlignment(Qt.AlignmentFlag.AlignLeft)
        return edit

    def selected_name_field(self) -> str:
        return next(
            field for field, radio in self.name_radios.items() if radio.isChecked()
        )

    def selected_person_field(self) -> str | None:
        return next(
            (field for field, radio in self.person_radios.items() if radio.isChecked()),
            None,
        )

    def selected_fields(self) -> frozenset[str]:
        fields: set[str] = set()
        if self.year_checkbox.isChecked() and self.year_combo.currentData() is not None:
            fields.add("year")
        if self.tags_checkbox.isChecked() and self._selected_tags:
            fields.add("tags")
        if self.qty_checkbox.isChecked() and self.qty_value.value() >= 0:
            fields.add("qty_played")
        if self.date_checkbox.isChecked() and self.date_start.date() != _UNSET_DATE:
            fields.add("last_played")
        return frozenset(fields)

    @property
    def selected_tags(self) -> list[str]:
        return list(getattr(self, "_selected_tags", []))

    def set_selected_tags(self, tags: list[str]) -> None:
        self._selected_tags = list(tags)
        self.selected_tags_container.clear()
        self.selected_tags_container.setVisible(bool(tags))
        colors = getattr(self, "_tag_colors", {})
        for tag in tags:
            color = colors.get(tag.casefold(), "#808080")
            chip = self._make_chip(
                tag,
                f"Remove tag '{tag}'",
                lambda current=tag: self.tag_remove_requested.emit(current),
                color=color,
            )
            self.selected_tags_container.flow_layout.addWidget(chip)
        self.selected_tags_container.refresh_height()
        self.criteria_changed.emit()

    def set_tag_colors(self, colors: dict[str, str]) -> None:
        self._tag_colors = dict(colors)
        self.set_selected_tags(self.selected_tags)

    def qty_criteria(self) -> tuple[str, int | None]:
        return (
            self.qty_operator.currentText(),
            self.qty_value.value() if self.qty_value.value() >= 0 else None,
        )

    def date_criteria(self) -> tuple[str, str | None]:
        operator = self.date_operator.currentText()
        start = (
            None
            if self.date_start.date() == _UNSET_DATE
            else self.date_start.date().toString("yyyy-MM-dd")
        )
        return operator, start

    def clear_values(self) -> None:
        for query in self.person_inputs.values():
            query.clear()
        self.year_combo.setCurrentIndex(0)
        self.set_selected_tags([])
        self.qty_value.setValue(-1)
        self.date_start.setDate(QDate.currentDate())
        self.date_checkbox.setChecked(False)
        self.criteria_changed.emit()

    def collect_criteria_as_filters(self) -> list[dict[str, str]]:
        """Collect the current search criteria as a list of filter dicts."""
        filters: list[dict[str, str]] = []
        fields = self.selected_fields()

        # Map name field to filter type
        name_field = self.selected_name_field()
        name_field_map = {
            "movie_name": "Title",
            "folder_name": "Folder",
            "file_name": "File",
        }
        filter_type = name_field_map.get(name_field, "Title")

        # Check if there's a search query in the parent widget
        parent_widget = self.parent()
        if parent_widget is not None and hasattr(parent_widget, "media_nav_search_box"):
            query = parent_widget.media_nav_search_box.text().strip()  # type: ignore[attr-defined]  # ty: ignore[unresolved-attribute]
            if query:
                filters.append({"filter": filter_type, "value": query})

        # Person field (actor/director)
        person_field = self.selected_person_field()
        if person_field:
            person_query = self.person_inputs[person_field].text().strip()
            if person_query:
                person_filter_map = {"actor": "Actor", "director": "Director"}
                filters.append(
                    {
                        "filter": person_filter_map[person_field],
                        "value": person_query,
                    }
                )

        # Year
        if "year" in fields:
            year = self.year_combo.currentData()
            if year is not None:
                operator = self.year_operator.currentText()
                filters.append(
                    {
                        "filter": "Year",
                        "value": f"custom|{operator}|{year}",
                    }
                )

        # Tags
        if "tags" in fields:
            for tag in self.selected_tags:
                filters.append({"filter": "Tag", "value": tag})

        # Qty Played
        if "qty_played" in fields:
            operator, value = self.qty_criteria()
            if value is not None:
                filters.append(
                    {
                        "filter": "Qty Played",
                        "value": f"custom|{operator}|{value}",
                    }
                )

        # Last Played
        if "last_played" in fields:
            operator, start = self.date_criteria()
            if start is not None:
                filters.append(
                    {
                        "filter": "Last Played",
                        "value": f"custom|{operator}|{start}",
                    }
                )

        return filters

    def _on_create_filter(self) -> None:
        """Emit signal with collected search criteria as filters."""
        filters = self.collect_criteria_as_filters()
        self.create_filter_requested.emit(filters)

    @staticmethod
    def _make_chip(
        label: str,
        tooltip: str,
        on_click: Callable[[], None],
        *,
        color: str | None = None,
    ) -> QToolButton:
        chip = TagButton()
        chip.setText(f"{label}  x")
        chip.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        chip.setToolTip(tooltip)
        chip.setCursor(Qt.CursorShape.PointingHandCursor)
        if color:
            chip.setStyleSheet(
                f"QToolButton {{ color: {get_contrast_text_color(color)}; "
                f"background-color: {color}; border-radius: 4px; padding: 2px 6px; }}"
            )
        else:
            chip.setStyleSheet(
                "QToolButton { border: 1px solid palette(mid); "
                "border-radius: 4px; padding: 2px 6px; }"
            )
        chip.clicked.connect(lambda _checked=False: on_click())
        return chip


class MediaNavSearchWidget(QWidget):
    search_requested = Signal(object)
    clear_search_requested = Signal()
    create_filter_requested = Signal(list)  # list of filter dicts

    def __init__(
        self, settings: _SearchSettings, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self._selected_tags: list[str] = []
        self._tag_picker: TagPickerDialog | None = None
        self._options_dialog: MediaNavSearchOptionsDialog | None = None

        self.media_nav_search_box = QLineEdit(self)
        self.media_nav_search_box.setObjectName("media_nav_search_box")
        self.media_nav_search_box.setPlaceholderText("Search movie name")
        self.media_nav_search_box.returnPressed.connect(self.submit_search)

        self.search_button = self._make_button("Search", "fa6s.magnifying-glass")
        self.options_button = self._make_button("Search Options", "fa6s.sliders")
        self.tag_button = self._make_button("Tags", "fa6s.tag")
        self.clear_search_button = self._make_button("Clear Search", "fa6s.xmark")
        self.search_button.setObjectName("media_nav_search_button")
        self.options_button.setObjectName("media_nav_search_options_button")
        self.clear_search_button.setObjectName("media_nav_clear_search_button")
        self.search_button.clicked.connect(self.submit_search)
        self.options_button.clicked.connect(self._show_options)
        self.tag_button.clicked.connect(self._show_tag_picker)
        self.clear_search_button.clicked.connect(self.clear_search)

        self.criteria_summary = _ChipContainer(self)
        self.selected_tags_container = self.criteria_summary
        self.status_label = QLabel(self)
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)

        # Create Filter button (hidden until criteria chips are shown)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.media_nav_search_box, 1)
        row.addWidget(self.search_button)
        row.addWidget(self.options_button)
        row.addWidget(self.tag_button)
        row.addWidget(self.clear_search_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addLayout(row)
        layout.addWidget(self.criteria_summary)
        layout.addWidget(self.status_label)

        self._build_options_dialog()

    @property
    def options_dialog(self) -> MediaNavSearchOptionsDialog:
        if self._options_dialog is None:
            raise RuntimeError("Media search options dialog is not initialized.")
        return self._options_dialog

    @staticmethod
    def _make_button(label: str, icon_name: str) -> QToolButton:
        button = QToolButton()
        button.setToolTip(label)
        button.setIcon(APP_THEME.icon(icon_name, color=APP_THEME.text_color))
        button.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
        button.setFixedSize(36, 32)
        return button

    def _build_options_dialog(self) -> None:
        self._options_dialog = MediaNavSearchOptionsDialog(self.window())
        self._options_dialog.select_tags_button.clicked.connect(self._show_tag_picker)
        self._options_dialog.tag_remove_requested.connect(self.remove_selected_tag)
        self._options_dialog.criteria_changed.connect(self._refresh_criteria_summary)
        self._options_dialog.create_filter_requested.connect(
            self.create_filter_requested
        )
        for radio in self.options_dialog.name_radios.values():
            radio.toggled.connect(self._update_search_placeholder)
        self._update_search_placeholder()

    def _show_options(self) -> None:
        self._show_popup(self.options_dialog, self.options_button)

    def _show_tag_picker(self) -> None:
        if self._tag_picker is None:
            self._tag_picker = TagPickerDialog(
                self.window(), allow_create=False, allow_delete=False
            )
            self._tag_picker.tag_selected.connect(self.add_selected_tag)
        tag_store = getattr(self.settings, "tag_store", None)
        catalog = (
            tag_store.list_tags()
            if tag_store is not None
            else self.settings.settings_data_model.tags
        )
        colors = {
            item["tag"].casefold(): item.get("color", "#808080")
            for item in catalog
            if isinstance(item, dict) and item.get("tag")
        }
        counts = tag_store.get_tag_counts() if tag_store is not None else {}
        self._tag_picker.set_data(self._selected_tags, colors, catalog, counts)
        self.options_dialog.set_tag_colors(colors)
        self._show_popup(self._tag_picker, self.options_dialog.select_tags_button)

    @staticmethod
    def _show_popup(popup: QDialog, anchor: QWidget) -> None:
        pos = anchor.mapToGlobal(anchor.rect().bottomLeft())
        screen = anchor.screen()
        if screen is not None:
            available = screen.availableGeometry()
            popup_size = popup.sizeHint()
            width = min(popup_size.width(), available.width() - 20)
            height = min(popup_size.height(), available.height() - 20)
            popup.resize(width, height)
            x = min(pos.x(), available.right() - width - 10)
            y = min(pos.y(), available.bottom() - height - 10)
            popup.move(max(x, available.left()), max(y, available.top()))
        else:
            popup.move(pos)
        popup.show()
        popup.raise_()
        popup.activateWindow()

    def _update_search_placeholder(self, *_args) -> None:
        field = self.options_dialog.selected_name_field()
        self.media_nav_search_box.setPlaceholderText(
            f"Search {_NAME_LABELS[field].lower()}"
        )

    def add_selected_tag(self, tag: str) -> None:
        if tag and tag.casefold() not in {
            item.casefold() for item in self._selected_tags
        }:
            self._selected_tags.append(tag)
            self.options_dialog.tags_checkbox.setChecked(True)
            self.options_dialog.set_selected_tags(self._selected_tags)
            self._refresh_criteria_summary()

    def remove_selected_tag(self, tag: str) -> None:
        self._selected_tags = [
            item for item in self._selected_tags if item.casefold() != tag.casefold()
        ]
        self.options_dialog.set_selected_tags(self._selected_tags)
        self._refresh_criteria_summary()

    def _refresh_criteria_summary(self, *_args) -> None:
        summary = self.criteria_summary
        summary.clear()
        options = self.options_dialog
        fields = options.selected_fields()
        criteria: list[tuple[str, str, Callable[[], None]]] = []

        person_field = options.selected_person_field()
        if person_field:
            query = options.person_inputs[person_field].text().strip()
            if query:
                label = _PERSON_LABELS[person_field]
                criteria.append(
                    (
                        f"{label}: {query}",
                        f"Clear {label.lower()} criterion",
                        lambda selected=person_field: options.person_inputs[
                            selected
                        ].clear(),
                    )
                )
        if "year" in fields:
            year = options.year_combo.currentData()
            criteria.append(
                (
                    f"Year {options.year_operator.currentText()} {year}",
                    "Clear year criterion",
                    lambda: options.year_combo.setCurrentIndex(0),
                )
            )
        if "tags" in fields:
            for tag in options.selected_tags:
                criteria.append(
                    (
                        f"Tag: {tag}",
                        f"Remove tag '{tag}'",
                        lambda selected=tag: self.remove_selected_tag(selected),
                    )
                )
        if "qty_played" in fields:
            operator, value = options.qty_criteria()
            criteria.append(
                (
                    f"Qty Played {operator} {value}",
                    "Clear Qty Played criterion",
                    lambda: options.qty_checkbox.setChecked(False),
                )
            )
        if "last_played" in fields:
            operator, start = options.date_criteria()
            label = f"Date Last Played {operator} {start}"
            criteria.append(
                (
                    label,
                    "Clear Date Last Played criterion",
                    lambda: options.date_checkbox.setChecked(False),
                )
            )

        for label, tooltip, callback in criteria:
            chip = MediaNavSearchOptionsDialog._make_chip(label, tooltip, callback)
            summary.flow_layout.addWidget(chip)
        has_criteria = bool(criteria)
        summary.setVisible(has_criteria)
        summary.refresh_height()

    def submit_search(self) -> None:
        options = self.options_dialog
        fields = options.selected_fields()
        qty_operator = qty_value = None
        date_operator = date_start = None
        if "qty_played" in fields:
            qty_operator, qty_value = options.qty_criteria()
        if "last_played" in fields:
            date_operator, date_start = options.date_criteria()

        selected_person_field = options.selected_person_field()
        criteria = MediaNavSearchCriteria(
            query=self.media_nav_search_box.text(),
            fields=fields,
            tags=tuple(options.selected_tags) if "tags" in fields else (),
            name_field=options.selected_name_field(),
            secondary_field=selected_person_field,
            secondary_query=(
                options.person_inputs[selected_person_field].text()
                if selected_person_field is not None
                else ""
            ),
            year=options.year_combo.currentData() if "year" in fields else None,
            year_operator=options.year_operator.currentText(),
            qty_operator=qty_operator,
            qty_value=qty_value,
            date_operator=date_operator,
            date_start=date_start,
        )
        self.show_error("")
        if not criteria.has_criteria:
            self.clear_search_requested.emit()
            return
        self.search_requested.emit(criteria)

    def clear_search(self) -> None:
        self.media_nav_search_box.clear()
        self._selected_tags.clear()
        self.options_dialog.clear_values()
        self._refresh_criteria_summary()
        self.show_error("")
        self.clear_search_requested.emit()

    def show_error(self, message: str) -> None:
        self.status_label.setText(message)
        self.status_label.setVisible(bool(message))
