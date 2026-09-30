from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QDate, QEvent, Qt
from PySide6.QtTest import QTest

from MyVideoExplorer.db.db_play_history import DbPlayHistory
from MyVideoExplorer.db.models.play_history import PlayHistory
from MyVideoExplorer.media_info_side.media_info_side_view import MediaInfoSideView
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.utils.str_util import StrUtil


class TestMediaInfoSideView:
    @pytest.fixture
    def mock_nfo_data(self):
        return {
            "title": "Test Movie",
            "year": 2024,
            "plot": "A test plot for a test movie.",
            "genres": ["Action", "Sci-Fi"],
            "actors": [{"name": "Actor A", "role": "Hero"}],
            "director": "Director X",
            "rating": 8.5,
            "runtime": 120,
            "ids": [{"site": "imdb", "id": "tt1234567"}],
        }

    @pytest.fixture
    def media_info_side_view(self, qtbot):
        nfo_parse_util = MagicMock(spec=NfoParseUtil)
        str_util = MagicMock(spec=StrUtil)
        str_util.join_strings.side_effect = lambda items: ", ".join(map(str, items))
        mock_log = MagicMock()

        view = MediaInfoSideView(nfo_parse_util, str_util, mock_log)
        qtbot.addWidget(view)
        return view

    def test_initialization(self, media_info_side_view):
        assert media_info_side_view.nfo_parse_util is not None

    def test_refresh_calls_nfo_parse(self, media_info_side_view, mock_nfo_data):
        media_info_side_view.nfo_parse_util.parse_nfo.return_value = mock_nfo_data

        with patch.object(media_info_side_view, "build_from_movie_info") as mock_build:
            media_info_side_view.refresh("/some/path")
            media_info_side_view.nfo_parse_util.parse_nfo.assert_called_with(
                folder_path="/some/path"
            )
            mock_build.assert_called_with(mock_nfo_data)

    def test_build_from_movie_info(self, media_info_side_view, mock_nfo_data):
        media_info_side_view.build_from_movie_info(mock_nfo_data)

        # Verify plot text
        assert (
            media_info_side_view.plot_section.get_plot_text().toPlainText()
            == mock_nfo_data["plot"]
        )

        # Verify some labels exist
        from PySide6.QtWidgets import QLabel

        labels = media_info_side_view.findChildren(QLabel)
        texts = [label.text() for label in labels]
        assert any("Score" in t for t in texts)
        assert any("8.5" in t for t in texts)

    def test_clear_nfo(self, media_info_side_view, mock_nfo_data):
        media_info_side_view.build_from_movie_info(mock_nfo_data)
        media_info_side_view.clear_nfo()

        from PySide6.QtWidgets import QLabel

        labels = media_info_side_view.findChildren(QLabel)
        texts = [label.text() for label in labels]
        assert any("No NFO data found" in t for t in texts)

    def test_meta_and_nfo_columns_collapse_and_expand(self, media_info_side_view):
        content = media_info_side_view.side_content_widget
        media_info_side_view.build_from_movie_info({"title": "Film"})
        expanded_meta_width = content.meta_widget.width()
        expanded_nfo_width = content.nfo_widget.width()
        expanded_panel_width = media_info_side_view.width()

        content.meta_collapse_button.click()
        assert content.meta_body_widget.isHidden()
        assert content.meta_widget.width() < expanded_meta_width
        assert content.nfo_widget.width() == expanded_nfo_width
        assert media_info_side_view.width() < expanded_panel_width

        content.header_widget.collapse_button.click()

        assert content.nfo_body_widget.isHidden()
        assert content.header_widget.title_label.isHidden()
        assert content.header_widget.collapse_button.text() == "I"
        assert not content.header_widget.collapse_button.icon().isNull()
        assert content.meta_title.isHidden()
        assert content.meta_collapse_button.text() == "M"
        assert not content.meta_collapse_button.icon().isNull()
        assert content.header_widget.collapse_button.width() == 40
        assert content.meta_collapse_button.width() == 40
        assert content.header_widget.collapse_button.height() == 28
        assert content.meta_collapse_button.height() == 28
        assert content.header_widget.collapse_button.iconSize().width() == 16
        assert content.meta_collapse_button.iconSize().width() == 16
        assert (
            content.nfo_widget.width() == content.header_widget.collapse_button.width()
        )

        content.header_widget.collapse_button.click()
        content.meta_collapse_button.click()

        assert not content.meta_body_widget.isHidden()
        assert not content.nfo_body_widget.isHidden()
        assert not content.header_widget.title_label.isHidden()
        assert content.header_widget.collapse_button.text() == ""
        assert not content.header_widget.collapse_button.icon().isNull()
        assert not content.meta_title.isHidden()
        assert content.meta_collapse_button.text() == ""
        assert not content.meta_collapse_button.icon().isNull()
        assert content.header_widget.collapse_button.width() == 40
        assert content.meta_collapse_button.width() == 40
        assert content.nfo_widget.width() == expanded_nfo_width

    def test_play_video_signal(self, media_info_side_view, mock_nfo_data, qtbot):
        media_info_side_view.build_from_movie_info(mock_nfo_data)

        with qtbot.waitSignal(
            media_info_side_view.info_side_play_video_btn_clicked
        ) as blocker:
            media_info_side_view.play_video()

        assert blocker.signal_triggered

    def test_apply_theme(self, media_info_side_view, mock_nfo_data):
        media_info_side_view.build_from_movie_info(mock_nfo_data)
        media_info_side_view.apply_theme()
        assert media_info_side_view.styleSheet() != ""

    def test_play_history_controls_load_and_save(self, qtbot):
        nfo_parse_util = MagicMock(spec=NfoParseUtil)
        str_util = MagicMock(spec=StrUtil)
        history = MagicMock(spec=DbPlayHistory)
        history.get_history.return_value = PlayHistory(3, date(2022, 8, 9))
        history.set_qty_played.return_value = True
        history.set_last_played.return_value = True
        view = MediaInfoSideView(nfo_parse_util, str_util, MagicMock(), history)
        qtbot.addWidget(view)

        view.set_media_file_path("C:/movies/film.mkv")

        assert view.side_content_widget.played_spin_box.value() == 3
        played_spin_box = view.side_content_widget.played_spin_box
        assert played_spin_box.alignment() & Qt.AlignmentFlag.AlignRight
        assert played_spin_box.width() >= 90
        assert played_spin_box.lineEdit().width() >= (
            played_spin_box.fontMetrics().horizontalAdvance("1234")
        )
        played_index = view.side_content_widget.meta_body_layout.indexOf(
            played_spin_box
        )
        played_item = view.side_content_widget.meta_body_layout.itemAt(played_index)
        assert played_item is not None
        assert played_item.alignment() & Qt.AlignmentFlag.AlignRight
        assert view.side_content_widget.last_played_date_edit.date() == QDate(
            2022, 8, 9
        )
        view.side_content_widget.played_spin_box.setValue(4)
        view.side_content_widget.last_played_date_edit.setDate(QDate(2023, 1, 2))

        history.set_qty_played.assert_called_once_with("C:/movies/film.mkv", 4)
        history.set_last_played.assert_called_once_with(
            "C:/movies/film.mkv", date(2023, 1, 2)
        )
        QTest.keyClick(
            view.side_content_widget.last_played_date_edit, Qt.Key.Key_Delete
        )
        assert history.set_last_played.call_args.args == (
            "C:/movies/film.mkv",
            None,
        )
        date_edit = view.side_content_widget.last_played_date_edit
        assert date_edit.width() >= (
            date_edit.fontMetrics().horizontalAdvance("0000-00-00") + 30
        )
        assert view.side_content_widget.meta_widget.width() == date_edit.width()

    def test_last_played_calendar_defaults_to_today_when_unset(self, qtbot):
        from MyVideoExplorer.media_info_side.media_info_side_content_widget import (
            LastPlayedDateEdit,
        )

        date_edit = LastPlayedDateEdit()
        date_edit.setMinimumDate(QDate(1900, 1, 1))
        date_edit.setDate(date_edit.minimumDate())
        qtbot.addWidget(date_edit)

        calendar = date_edit.calendarWidget()
        date_edit.eventFilter(calendar, QEvent(QEvent.Type.Show))
        QTest.qWait(10)

        assert calendar.selectedDate() == QDate.currentDate()
        assert date_edit.date() == date_edit.minimumDate()

        selected_date = QDate(2022, 8, 9)
        date_edit.setDate(selected_date)
        date_edit.eventFilter(calendar, QEvent(QEvent.Type.Show))
        QTest.qWait(10)
        assert calendar.selectedDate() == selected_date
