from datetime import date
from shutil import copyfile
from types import SimpleNamespace

import duckdb
import pytest
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QToolButton

from MyVideoExplorer.db.db_migrations import DbMigrations
from MyVideoExplorer.folder_list.media_nav_search import (
    MediaNavSearch,
    MediaNavSearchCriteria,
)
from MyVideoExplorer.folder_list.media_nav_search_widget import (
    MediaNavSearchWidget,
)


class _SearchSettings:
    def __init__(self, database_paths: list[str]) -> None:
        self.media_configs = [{"db_path": path} for path in database_paths]

    def db_enabled(self) -> bool:
        return bool(self.media_configs)

    @staticmethod
    def get_db_path(config: dict) -> str:
        return config["db_path"]


@pytest.fixture
def media_db(tmp_path):
    db_path = tmp_path / "media.duckdb"
    DbMigrations(str(db_path)).run_migrations()
    rows = [
        (
            "C:/Movies/Alpha/Alpha Film.mkv",
            "The Alpha Film",
            2001,
            ["A. Director"],
            ["A. Actor"],
            ["Drama"],
            ["Watched", "Favorite"],
            5,
            date(2024, 1, 15),
        ),
        (
            "C:/Movies/Beta/Beta Film.mkv",
            "Beta Story",
            2010,
            ["B. Director"],
            ["B. Actor"],
            ["Comedy"],
            ["Favorite"],
            2,
            date(2022, 5, 10),
        ),
    ]
    with duckdb.connect(str(db_path)) as connection:
        for (
            file_path,
            title,
            year,
            directors,
            actors,
            tags,
            user_tags,
            qty_played,
            last_played,
        ) in rows:
            connection.execute(
                """
                INSERT INTO media_file (
                    media_path, file_path, type, title, year, directors, actors,
                    tags, user_tags, qty_played, last_played
                ) VALUES (?, ?, 'video', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "C:/Movies",
                    file_path,
                    title,
                    year,
                    directors,
                    actors,
                    tags,
                    user_tags,
                    qty_played,
                    last_played,
                ),
            )
    return db_path


def _search(media_db) -> MediaNavSearch:
    return MediaNavSearch(_SearchSettings([str(media_db)]))


def test_search_ands_all_enabled_text_fields(media_db):
    results = _search(media_db).search(
        MediaNavSearchCriteria(
            query="alpha",
            name_field="movie_name",
            secondary_field="director",
            secondary_query="director",
        )
    )

    assert [(item.name, item.full_path) for item in results] == [
        ("Alpha", "C:/Movies/Alpha")
    ]

    no_match = _search(media_db).search(
        MediaNavSearchCriteria(
            query="alpha",
            name_field="movie_name",
            secondary_field="actor",
            secondary_query="b. actor",
        )
    )
    assert no_match == []


@pytest.mark.parametrize(
    ("name_field", "query"),
    [
        ("folder_name", "alpha"),
        ("file_name", "alpha film"),
        ("movie_name", "alpha film"),
    ],
)
def test_search_name_text_fields(media_db, name_field, query):
    results = _search(media_db).search(
        MediaNavSearchCriteria(query=query, name_field=name_field)
    )
    assert [item.name for item in results] == ["Alpha"]


@pytest.mark.parametrize(
    ("field", "query"),
    [("director", "a. director"), ("actor", "a. actor")],
)
def test_search_person_fields(media_db, field, query):
    results = _search(media_db).search(
        MediaNavSearchCriteria(
            query="",
            secondary_field=field,
            secondary_query=query,
        )
    )
    assert [item.name for item in results] == ["Alpha"]


def test_search_year_and_other_criteria_are_anded(media_db):
    results = _search(media_db).search(
        MediaNavSearchCriteria(
            query="",
            fields=frozenset({"year"}),
            year=2001,
        )
    )
    assert [item.name for item in results] == ["Alpha"]

    results_after_year = _search(media_db).search(
        MediaNavSearchCriteria(
            query="",
            fields=frozenset({"year"}),
            year=2005,
            year_operator="<",
        )
    )
    assert [item.name for item in results_after_year] == ["Alpha"]

    no_match = _search(media_db).search(
        MediaNavSearchCriteria(
            query="alpha",
            name_field="movie_name",
            fields=frozenset({"year"}),
            year=2010,
        )
    )
    assert no_match == []


@pytest.mark.parametrize(
    ("operator", "value", "expected"),
    [
        ("=", 2001, ["Alpha"]),
        ("!=", 2001, ["Beta"]),
        (">", 2001, ["Beta"]),
        (">=", 2001, ["Alpha", "Beta"]),
        ("<", 2010, ["Alpha"]),
        ("<=", 2001, ["Alpha"]),
    ],
)
def test_year_comparison_operators(media_db, operator, value, expected):
    results = _search(media_db).search(
        MediaNavSearchCriteria(
            query="",
            fields=frozenset({"year"}),
            year=value,
            year_operator=operator,
        )
    )
    assert [item.name for item in results] == expected


def test_search_only_uses_selected_person_radio(media_db):
    results = _search(media_db).search(
        MediaNavSearchCriteria(
            query="",
            secondary_field="actor",
            secondary_query="a. actor",
        )
    )
    assert [item.name for item in results] == ["Alpha"]


def test_search_ands_selected_tags_qty_and_date(media_db):
    results = _search(media_db).search(
        MediaNavSearchCriteria(
            query="",
            fields=frozenset({"tags", "qty_played", "last_played"}),
            tags=("Drama", "Watched"),
            qty_operator=">=",
            qty_value=5,
            date_operator=">=",
            date_start="2024-01-01",
        )
    )
    assert [item.name for item in results] == ["Alpha"]

    missing_tag = _search(media_db).search(
        MediaNavSearchCriteria(
            query="",
            fields=frozenset({"tags"}),
            tags=("Drama", "Comedy"),
        )
    )
    assert missing_tag == []


def test_search_spans_databases_and_deduplicates_folders(media_db, tmp_path):
    duplicate_db = tmp_path / "duplicate.duckdb"
    copyfile(media_db, duplicate_db)
    service = MediaNavSearch(
        _SearchSettings([str(media_db), str(duplicate_db), str(media_db)])
    )

    results = service.search(
        MediaNavSearchCriteria(
            query="alpha",
            name_field="folder_name",
        )
    )
    assert [item.full_path for item in results] == ["C:/Movies/Alpha"]


@pytest.mark.parametrize(
    ("operator", "value", "expected"),
    [
        ("=", 5, ["Alpha"]),
        ("!=", 5, ["Beta"]),
        (">", 2, ["Alpha"]),
        (">=", 5, ["Alpha"]),
        ("<", 5, ["Beta"]),
        ("<=", 2, ["Beta"]),
    ],
)
def test_qty_comparison_operators(media_db, operator, value, expected):
    results = _search(media_db).search(
        MediaNavSearchCriteria(
            query="",
            fields=frozenset({"qty_played"}),
            qty_operator=operator,
            qty_value=value,
        )
    )
    assert [item.name for item in results] == expected


def test_date_operator_uses_one_comparison_date(media_db):
    results = _search(media_db).search(
        MediaNavSearchCriteria(
            query="",
            fields=frozenset({"last_played"}),
            date_operator=">=",
            date_start="2023-01-01",
        )
    )
    assert [item.name for item in results] == ["Alpha"]


def test_search_rejects_missing_criteria_and_disabled_database():
    assert not MediaNavSearchCriteria(query="", fields=frozenset()).has_criteria

    with pytest.raises(RuntimeError, match="enabled, configured"):
        MediaNavSearch(_SearchSettings([])).search(
            MediaNavSearchCriteria(query="something", name_field="movie_name")
        )


@pytest.mark.parametrize(
    ("operator", "start", "expected"),
    [
        ("=", "2024-01-15", ["Alpha"]),
        ("!=", "2024-01-15", ["Beta"]),
        (">", "2022-05-10", ["Alpha"]),
        (">=", "2022-05-10", ["Alpha", "Beta"]),
        ("<", "2024-01-15", ["Beta"]),
        ("<=", "2022-05-10", ["Beta"]),
    ],
)
def test_date_comparison_operators(media_db, operator, start, expected):
    results = _search(media_db).search(
        MediaNavSearchCriteria(
            query="",
            fields=frozenset({"last_played"}),
            date_operator=operator,
            date_start=start,
        )
    )
    assert [item.name for item in results] == expected


def test_search_widget_defaults_submit_and_clear(qtbot):
    settings = _WidgetSettings()
    widget = MediaNavSearchWidget(settings)
    qtbot.addWidget(widget)

    assert widget.media_nav_search_box.objectName() == "media_nav_search_box"
    assert widget.options_dialog.selected_name_field() == "movie_name"

    widget.media_nav_search_box.setText("Alpha")
    widget.add_selected_tag("Drama")
    widget.options_dialog.qty_checkbox.setChecked(True)
    widget.options_dialog.qty_value.setValue(8)

    with qtbot.waitSignal(widget.search_requested) as blocker:
        widget.search_button.click()
    criteria = blocker.args[0]
    assert criteria.query == "Alpha"
    assert criteria.tags == ("Drama",)
    assert criteria.qty_value == 8
    assert criteria.fields == frozenset({"tags", "qty_played"})

    with qtbot.waitSignal(widget.search_requested) as enter_blocker:
        qtbot.keyClick(widget.media_nav_search_box, Qt.Key.Key_Return)
    assert enter_blocker.args[0].query == "Alpha"

    with qtbot.waitSignal(widget.clear_search_requested):
        widget.clear_search_button.click()
    assert widget.media_nav_search_box.text() == ""
    assert widget._selected_tags == []
    assert widget.options_dialog.qty_value.value() == -1
    assert widget.options_dialog.qty_checkbox.isChecked()
    assert widget.options_dialog.tags_checkbox.isChecked()
    assert widget.options_dialog.date_start.date() == QDate.currentDate()
    assert not widget.options_dialog.date_checkbox.isChecked()


def test_options_radio_groups_year_options_and_placeholder(qtbot):
    widget = MediaNavSearchWidget(_WidgetSettings())
    qtbot.addWidget(widget)
    options = widget.options_dialog

    assert options.selected_name_field() == "movie_name"
    assert list(options.name_radios) == ["movie_name", "folder_name", "file_name"]
    assert list(options.person_radios) == ["actor", "director"]
    assert options.name_group.exclusive()
    assert options.person_group.exclusive()
    assert options.person_inputs["director"].objectName() == "search_director_query"
    assert options.person_inputs["actor"].objectName() == "search_actor_query"
    assert widget.media_nav_search_box.placeholderText() == "Search movie name"

    options.name_radios["folder_name"].setChecked(True)
    assert options.selected_name_field() == "folder_name"
    assert widget.media_nav_search_box.placeholderText() == "Search folder name"

    years = [
        options.year_combo.itemData(index)
        for index in range(1, options.year_combo.count())
    ]
    this_year = QDate.currentDate().year()
    assert years == list(range(this_year, 1949, -1)) + [
        1940,
        1930,
        1920,
        1910,
        1900,
    ]
    assert [
        options.qty_operator.itemText(i) for i in range(options.qty_operator.count())
    ] == [
        "=",
        "!=",
        ">",
        ">=",
        "<",
        "<=",
    ]
    assert [
        options.year_operator.itemText(i) for i in range(options.year_operator.count())
    ] == ["=", "!=", ">", ">=", "<", "<="]
    assert options.qty_operator.width() < 70
    assert options.year_operator.width() < 70
    assert "QRadioButton::indicator:checked" in options.styleSheet()
    assert options.date_operator.findText("Between") == -1
    assert options.year_combo.itemText(0) == "- Any -"
    assert options.date_start.date() == QDate.currentDate()
    assert options.qty_value.width() >= (
        options.qty_value.fontMetrics().horizontalAdvance("00000") + 72
    )
    assert options.date_start.minimumWidth() >= (
        options.date_start.fontMetrics().horizontalAdvance("YYYY-MM-DD") + 48
    )
    assert (
        options.year_combo.itemData(0, Qt.ItemDataRole.TextAlignmentRole)
        == Qt.AlignmentFlag.AlignLeft
    )
    assert options.qty_value.lineEdit().alignment() == Qt.AlignmentFlag.AlignLeft
    assert options.date_start.lineEdit().alignment() == Qt.AlignmentFlag.AlignLeft
    assert (
        options.year_combo.width()
        <= max(
            options.year_combo.fontMetrics().horizontalAdvance(str(this_year)),
            options.year_combo.fontMetrics().horizontalAdvance("- Any -"),
        )
        + 60
    )
    assert options.name_radios["movie_name"].parentWidget() is options
    options.qty_value.setValue(12345)
    assert options.qty_value.lineEdit().text() == "12345"


def test_tags_are_visible_in_dialog_and_summary_and_removable(qtbot):
    widget = MediaNavSearchWidget(_WidgetSettings())
    qtbot.addWidget(widget)

    widget.add_selected_tag("Drama")
    assert widget.options_dialog.tags_checkbox.isChecked()
    assert widget.options_dialog.selected_tags_container.flow_layout.count() == 1
    assert widget.criteria_summary.flow_layout.count() == 1
    assert widget.criteria_summary.heightForWidth(200) > 0

    dialog_chip_item = widget.options_dialog.selected_tags_container.flow_layout.itemAt(
        0
    )
    assert dialog_chip_item is not None
    dialog_chip = dialog_chip_item.widget()
    assert isinstance(dialog_chip, QToolButton)
    dialog_chip.click()

    assert widget._selected_tags == []
    assert widget.options_dialog.selected_tags_container.flow_layout.count() == 0
    assert widget.criteria_summary.flow_layout.count() == 0


def test_active_filter_chips_expand_to_fit(qtbot):
    widget = MediaNavSearchWidget(_WidgetSettings())
    qtbot.addWidget(widget)
    options = widget.options_dialog
    options.person_inputs["director"].setText("A. Director")
    options.year_checkbox.setChecked(True)
    options.year_combo.setCurrentIndex(1)
    options.qty_checkbox.setChecked(True)
    options.qty_value.setValue(4)
    options.date_checkbox.setChecked(True)
    options.date_start.setDate(QDate(2024, 1, 1))
    widget.add_selected_tag("Drama")
    widget.add_selected_tag("Favorite")

    assert widget.criteria_summary.flow_layout.count() == 6
    assert widget.criteria_summary.heightForWidth(
        180
    ) > widget.criteria_summary.heightForWidth(1200)

    summary_item = widget.criteria_summary.flow_layout.itemAt(1)
    assert summary_item is not None
    summary_chip = summary_item.widget()
    assert isinstance(summary_chip, QToolButton)
    summary_chip.click()
    assert options.year_combo.currentData() is None
    assert widget.criteria_summary.flow_layout.count() == 5


def test_empty_search_restores_all_and_blank_query_keeps_active_filters(qtbot):
    widget = MediaNavSearchWidget(_WidgetSettings())
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.clear_search_requested):
        widget.search_button.click()

    widget.options_dialog.person_inputs["director"].setText("A. Director")
    with qtbot.waitSignal(widget.search_requested) as blocker:
        widget.search_button.click()
    criteria = blocker.args[0]
    assert criteria.query == ""
    assert criteria.secondary_field == "director"
    assert criteria.secondary_query == "A. Director"

    widget.options_dialog.person_radios["actor"].setChecked(True)
    widget.options_dialog.person_inputs["actor"].setText("A. Actor")
    with qtbot.waitSignal(widget.search_requested) as actor_blocker:
        widget.search_button.click()
    actor_criteria = actor_blocker.args[0]
    assert actor_criteria.secondary_field == "actor"
    assert actor_criteria.secondary_query == "A. Actor"


class _WidgetSettings:
    settings_data_model = SimpleNamespace(tags=[])
    tag_store = None
