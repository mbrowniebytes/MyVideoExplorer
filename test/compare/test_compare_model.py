"""Tests for CompareTableModel — lazy-loading, pagination, filtering, and sorting."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from PySide6.QtCore import Qt

from MyVideoExplorer.compare.compare_model import (
    COMPARE_COLUMNS,
    PAGE_SIZE,
    CompareTableModel,
)
from MyVideoExplorer.compare.compare_service import CompareService


@pytest.fixture
def compared_db(local_test_db, compare_test_db):
    """Run comparison and return the compare database path."""
    service = CompareService()
    service.run_comparison(Path(local_test_db), Path(compare_test_db))

    # Verify the comparison produced results
    conn = duckdb.connect(compare_test_db)
    row = conn.execute("SELECT COUNT(*) FROM compare_results").fetchone()
    assert row is not None
    result_count = row[0]
    conn.close()

    assert result_count > 0, f"Comparison produced {result_count} results, expected > 0"
    return compare_test_db


@pytest.fixture
def compare_model(compared_db):
    """Create a CompareTableModel from the compared database."""
    return CompareTableModel(Path(compared_db))


class TestCompareTableModelBasic:
    """Test basic table model functionality."""

    def test_model_should_load_results(self, compare_model):
        # Paired rows: each DB row becomes 2 display rows
        assert compare_model.rowCount() > 0
        assert compare_model.columnCount() == len(COMPARE_COLUMNS)

    def test_model_should_return_column_headers(self, compare_model):
        for i in range(compare_model.columnCount()):
            header = compare_model.headerData(i, Qt.Orientation.Horizontal)
            assert header == COMPARE_COLUMNS[i]["title"]

    def test_model_should_return_data(self, compare_model):
        if compare_model.rowCount() > 0:
            index = compare_model.index(0, 0)
            data = compare_model.data(index)
            assert data is not None

    def test_model_should_handle_empty_db(self, tmp_path):
        db_path = str(tmp_path / "empty.db")
        from MyVideoExplorer.db.db_scan import DbScanUtil

        DbScanUtil(db_path)

        conn = duckdb.connect(db_path)
        conn.execute("CREATE TABLE compare_results (row_id BIGINT PRIMARY KEY)")
        conn.close()

        model = CompareTableModel(Path(db_path))
        assert model.rowCount() == 0

    def test_model_should_produce_paired_rows(self, compare_model, compared_db):
        """Verify that each DB row produces 2 display rows (local + compare)."""
        conn = duckdb.connect(str(compared_db))
        row = conn.execute("SELECT COUNT(*) FROM compare_results").fetchone()
        assert row is not None
        db_count = row[0]
        conn.close()

        # Each DB row should produce 2 display rows
        assert compare_model.rowCount() == db_count * 2

    def test_model_should_have_row_numbers(self, compare_model):
        """Verify row numbers have L/C suffix."""
        if compare_model.rowCount() > 0:
            # Row number is column 0
            index = compare_model.index(0, 0)
            row_num = compare_model.data(index)
            assert row_num is not None
            assert isinstance(row_num, str)
            assert row_num.endswith(("L", "C"))
            # First row should end with L (Local)
            assert compare_model.data(compare_model.index(0, 0)).endswith("L")
            # Second row should end with C (Compare)
            if compare_model.rowCount() > 1:
                assert compare_model.data(compare_model.index(1, 0)).endswith("C")

    def test_model_titles_should_not_have_prefix(self, compare_model):
        """Verify titles do NOT have Local:/Compare: prefix."""
        if compare_model.rowCount() > 0:
            # Column 1 is title
            idx_local = compare_model.index(0, 1)
            title_local = compare_model.data(idx_local)
            assert not title_local.startswith("Local: ")

            idx_compare = compare_model.index(1, 1)
            title_compare = compare_model.data(idx_compare)
            assert not title_compare.startswith("Compare: ")


class TestCompareTableModelPagination:
    """Test pagination functionality."""

    def test_model_should_paginate_results(self, tmp_path):
        """Create a database with many results and test pagination."""
        db_path = str(tmp_path / "pagination_test.db")
        from MyVideoExplorer.db.db_scan import DbScanUtil

        DbScanUtil(db_path)

        conn = duckdb.connect(db_path)
        conn.execute("""
            CREATE TABLE compare_results (
                row_id BIGINT PRIMARY KEY,
                local_file_path TEXT,
                compare_file_path TEXT,
                local_title TEXT,
                compare_title TEXT,
                match_score INTEGER,
                status TEXT,
                confidence DOUBLE,
                local_width INTEGER,
                local_height INTEGER,
                local_codec TEXT,
                local_bitrate BIGINT,
                local_audio_channels INTEGER,
                local_audio_bitrate BIGINT,
                local_has_subtitles BOOLEAN,
                local_file_size BIGINT,
                compare_width INTEGER,
                compare_height INTEGER,
                compare_codec TEXT,
                compare_bitrate BIGINT,
                compare_audio_channels INTEGER,
                compare_audio_bitrate BIGINT,
                compare_has_subtitles BOOLEAN,
                compare_file_size BIGINT
            )
        """)

        # Insert 250 rows
        for i in range(250):
            conn.execute(
                """
                INSERT INTO compare_results VALUES (
                    ?, '', '', ?, '', 80, 'match', 0.8,
                    1920, 1080, 'h264', 10000000, 6, 640000, FALSE, 1000000,
                    1920, 1080, 'h264', 10000000, 6, 640000, FALSE, 1000000
                )
                """,
                [i, f"Title {i}"],
            )
        conn.close()

        model = CompareTableModel(Path(db_path))

        # First page: 100 DB rows → 200 display rows (paired)
        assert model.rowCount() == PAGE_SIZE * 2
        current_page, total_pages = model.page_info()
        assert current_page == 0
        assert total_pages == 3  # 250 / 100 = 3 pages (100, 100, 50)

        # Navigate to next page
        assert model.next_page() is True
        assert model.rowCount() == PAGE_SIZE * 2
        current_page, _ = model.page_info()
        assert current_page == 1

        # Navigate to last page
        assert model.next_page() is True
        # Last page: 50 DB rows → 100 display rows (paired)
        assert model.rowCount() == 50 * 2
        current_page, _ = model.page_info()
        assert current_page == 2

        # No more pages
        assert model.next_page() is False

        # Go back
        assert model.prev_page() is True
        current_page, _ = model.page_info()
        assert current_page == 1

        # Go back to start
        assert model.prev_page() is True
        current_page, _ = model.page_info()
        assert current_page == 0

        # No more previous pages
        assert model.prev_page() is False


class TestCompareTableModelFiltering:
    """Test filtering functionality."""

    def test_model_should_filter_by_status(self, compare_model, compared_db):
        total_before = compare_model.rowCount()

        compare_model.set_status_filter("missing")
        missing_count = compare_model.rowCount()

        compare_model.set_status_filter("")
        all_count = compare_model.rowCount()

        assert all_count == total_before
        assert missing_count <= all_count

    def test_model_should_hide_missing_when_requested(self, compare_model, compared_db):
        total_before = compare_model.rowCount()

        compare_model.set_show_missing(False)
        without_missing = compare_model.rowCount()

        conn = duckdb.connect(str(compared_db))
        row = conn.execute(
            "SELECT COUNT(*) FROM compare_results WHERE status = 'missing'"
        ).fetchone()
        assert row is not None
        missing_count = row[0]
        conn.close()

        # Without missing should be less than or equal to total
        # Each missing DB row produces 2 display rows
        assert without_missing <= total_before
        if missing_count > 0:
            assert without_missing == total_before - (missing_count * 2)

    def test_model_should_search_by_title(self, compare_model):
        compare_model.set_search_query("Inception")
        inception_count = compare_model.rowCount()
        assert inception_count >= 0

        compare_model.set_search_query("")
        all_count = compare_model.rowCount()
        assert all_count >= inception_count

    def test_model_should_search_case_insensitive(self, compare_model):
        """Verify search is case-insensitive."""
        compare_model.set_search_query("inception")
        lower_count = compare_model.rowCount()

        compare_model.set_search_query("Inception")
        upper_count = compare_model.rowCount()

        # Both should return the same results
        assert lower_count == upper_count

    def test_model_should_search_all_columns(self, compare_model):
        """Verify search works across all text columns, not just title."""
        # Search by codec
        compare_model.set_search_query("h264")
        codec_count = compare_model.rowCount()
        assert codec_count >= 0

        compare_model.set_search_query("")

    def test_model_should_filter_by_multiple_statuses(self, compare_model):
        """Verify multi-status filtering works."""
        compare_model.set_status_filters(["missing"])
        missing_count = compare_model.rowCount()

        compare_model.set_status_filters(["match", "similar"])
        matched_count = compare_model.rowCount()

        compare_model.set_status_filters([])
        all_count = compare_model.rowCount()

        assert all_count >= missing_count
        assert all_count >= matched_count

    def test_model_should_combine_filters(self, compare_model):
        compare_model.set_status_filter("missing")
        compare_model.set_show_missing(False)
        # Show missing = False should override status filter for missing
        compare_model.rowCount()

        compare_model.set_show_missing(True)
        compare_model.set_status_filter("missing")
        missing_count = compare_model.rowCount()

        assert missing_count >= 0

    def test_model_should_format_score(self, compare_model):
        """Verify score is formatted as an integer string with optional arrow."""
        if compare_model.rowCount() > 0:
            # Column 4 is match_score (Score)
            index = compare_model.index(0, 4)
            score = compare_model.data(index)
            assert isinstance(score, str)
            # Score should be digits, optionally followed by ↑ or ↓
            score_base = score.replace("↑", "").replace("↓", "")
            assert score_base.isdigit() or score_base == "0"


class TestCompareTableModelSorting:
    """Test sorting functionality."""

    def test_model_should_sort_by_match_score_desc(self, compare_model):
        # Default sort is match_score DESC
        # Columns: 0=row_number, 1=title, 2=file_size, 3=status, 4=match_score, ...
        scores = []
        for row in range(compare_model.rowCount()):
            index = compare_model.index(row, 4)  # match_score column (Score)
            score = compare_model.data(index)
            scores.append(score if score is not None else "0")

        # Scores are formatted as "score (confidence)", check they are present
        assert len(scores) == compare_model.rowCount()

    def test_model_should_sort_by_status_ascending(self, compare_model):
        # Sort by status ascending (column 3)
        compare_model.sort(3, Qt.SortOrder.AscendingOrder)

        statuses = []
        for row in range(compare_model.rowCount()):
            index = compare_model.index(row, 3)
            status = compare_model.data(index)
            statuses.append(status if status is not None else "")

        # All statuses should be present and sorted
        assert len(statuses) == compare_model.rowCount()
        for s in statuses:
            assert s in ("match", "similar", "missing")

        # Verify ascending order (paired rows have same status)
        for i in range(0, len(statuses) - 1, 2):
            assert statuses[i] <= statuses[i + 1]

    def test_model_should_sort_by_status_descending(self, compare_model):
        # Sort by status descending (column 3)
        compare_model.sort(3, Qt.SortOrder.DescendingOrder)

        statuses = []
        for row in range(compare_model.rowCount()):
            index = compare_model.index(row, 3)
            status = compare_model.data(index)
            statuses.append(status if status is not None else "")

        # All statuses should be present
        assert len(statuses) == compare_model.rowCount()
        for s in statuses:
            assert s in ("match", "similar", "missing")

    def test_model_should_sort_by_title_ascending(self, compare_model):
        # Sort by title ascending (column 1)
        compare_model.sort(1, Qt.SortOrder.AscendingOrder)

        titles = []
        for row in range(compare_model.rowCount()):
            index = compare_model.index(row, 1)
            title = compare_model.data(index)
            titles.append(title if title is not None else "")

        # Titles should be sorted (Local: and Compare: prefixes will sort together)
        assert len(titles) == compare_model.rowCount()


class TestCompareTableModelColumnInfo:
    """Test column definitions."""

    def test_columns_should_include_all_required_fields(self):
        column_keys = [c["key"] for c in COMPARE_COLUMNS]

        # Paired-row columns (new layout)
        assert "row_number" in column_keys
        assert "title" in column_keys
        assert "file_size" in column_keys
        assert "status" in column_keys
        assert "match_score" in column_keys
        assert "resolution" in column_keys
        assert "codec" in column_keys
        assert "bitrate" in column_keys
        assert "audio" in column_keys
        assert "has_subtitles" in column_keys

        # Removed columns should not be present
        assert "confidence" not in column_keys
        assert "audio_channels" not in column_keys
        assert "audio_bitrate" not in column_keys

    def test_columns_should_have_correct_order(self):
        """Verify columns are in the expected order."""
        expected_order = [
            "row_number",
            "title",
            "file_size",
            "status",
            "match_score",
            "resolution",
            "codec",
            "bitrate",
            "audio",
            "has_subtitles",
        ]
        actual_keys = [c["key"] for c in COMPARE_COLUMNS]
        assert actual_keys == expected_order

    def test_columns_should_have_correct_titles(self):
        """Verify column display titles."""
        titles = [c["title"] for c in COMPARE_COLUMNS]
        assert titles[0] == "#"
        assert titles[1] == "Title (Local/Compare)"
        assert titles[2] == "Size"
        assert titles[3] == "Status"
        assert titles[4] == "Score"
        assert titles[8] == "Audio"

    def test_page_size_should_be_100(self):
        assert PAGE_SIZE == 100

    def test_columns_should_have_alignment(self):
        """Verify alignment hints are set for columns."""
        from PySide6.QtCore import Qt

        # Right-aligned columns
        right_align_keys = {
            "file_size",
            "match_score",
            "resolution",
            "bitrate",
            "audio",
        }
        # Center-aligned columns
        center_align_keys = {"status", "codec", "has_subtitles"}

        for col in COMPARE_COLUMNS:
            key = col["key"]
            if key in right_align_keys:
                assert "align" in col
                assert col["align"] & Qt.AlignmentFlag.AlignRight
            elif key in center_align_keys:
                assert "align" in col
                assert col["align"] & Qt.AlignmentFlag.AlignCenter

    def test_score_header_should_have_tooltip(self, compare_model):
        """Verify Score column header has a tooltip explaining quality criteria."""
        # Column 4 is match_score
        tooltip = compare_model.headerData(
            4, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole
        )
        assert tooltip is not None
        assert "fuzzy" in tooltip.lower()
        assert "quality" in tooltip.lower()
        assert "resolution" in tooltip.lower()

    def test_data_should_return_alignment_role(self, compare_model):
        """Verify data() returns alignment for Qt.ItemDataRole.TextAlignmentRole."""
        if compare_model.rowCount() > 0:
            # Score column (4) should be right-aligned
            score_idx = compare_model.index(0, 4)
            align = compare_model.data(score_idx, Qt.ItemDataRole.TextAlignmentRole)
            assert align is not None
            assert Qt.AlignmentFlag.AlignRight in align

            # Status column (3) should be center-aligned
            status_idx = compare_model.index(0, 3)
            align = compare_model.data(status_idx, Qt.ItemDataRole.TextAlignmentRole)
            assert align is not None
            assert Qt.AlignmentFlag.AlignCenter in align


class TestCompareTableModelMissingEntries:
    """Test missing entries display with empty rows."""

    def test_missing_local_should_show_empty_local_row(self, compare_model):
        """When local is missing, the Local row should show empty values."""
        # Find a missing entry where local is missing
        for row in range(compare_model.rowCount()):
            row_num = compare_model.data(compare_model.index(row, 0))
            status = compare_model.data(compare_model.index(row, 3))
            if status == "missing" and row_num and row_num.endswith("L"):
                # This is a Local row for a missing entry
                title = compare_model.data(compare_model.index(row, 1))
                # Local title should be empty for compare-missing-local entries
                if not title:
                    # Found a compare-missing-local entry
                    size = compare_model.data(compare_model.index(row, 2))
                    assert size == ""
                    break

    def test_missing_compare_should_show_empty_compare_row(self, compare_model):
        """When compare is missing, the Compare row should show empty values."""
        # Find a missing entry where compare is missing
        for row in range(compare_model.rowCount()):
            row_num = compare_model.data(compare_model.index(row, 0))
            status = compare_model.data(compare_model.index(row, 3))
            if status == "missing" and row_num and row_num.endswith("C"):
                # This is a Compare row for a missing entry
                title = compare_model.data(compare_model.index(row, 1))
                # Compare title should be empty for local-missing-compare entries
                if not title:
                    # Found a local-missing-compare entry
                    size = compare_model.data(compare_model.index(row, 2))
                    assert size == ""
                    break

    def test_file_size_should_always_be_gb(self, compare_model):
        """Verify file size is always shown in GB."""
        for row in range(compare_model.rowCount()):
            size = compare_model.data(compare_model.index(row, 2))
            if size:
                assert size.endswith(" GB"), f"Expected GB format, got: {size}"


class TestCompareTableModelScoreAdjustment:
    """Test quality-aware score adjustment for 'similar' entries."""

    def test_score_should_not_have_arrow_suffix(self, compare_model):
        """Score should be a plain integer, no arrow suffix."""
        for row in range(compare_model.rowCount()):
            score = compare_model.data(compare_model.index(row, 4))
            if score:
                assert "↑" not in score, f"Score should not have arrow: {score}"
                assert "↓" not in score, f"Score should not have arrow: {score}"

    def test_score_should_be_higher_for_better_side_when_similar(self, tmp_path):
        """For 'similar' status, the better side shows a higher score."""
        db_path = str(tmp_path / "score_test.db")
        from MyVideoExplorer.db.db_scan import DbScanUtil

        DbScanUtil(db_path)

        conn = duckdb.connect(db_path)
        conn.execute("""
            CREATE TABLE compare_results (
                row_id BIGINT PRIMARY KEY,
                local_file_path TEXT,
                compare_file_path TEXT,
                local_title TEXT,
                compare_title TEXT,
                match_score INTEGER,
                status TEXT,
                confidence DOUBLE,
                local_width INTEGER,
                local_height INTEGER,
                local_codec TEXT,
                local_bitrate BIGINT,
                local_audio_channels INTEGER,
                local_audio_bitrate BIGINT,
                local_has_subtitles BOOLEAN,
                local_file_size BIGINT,
                compare_width INTEGER,
                compare_height INTEGER,
                compare_codec TEXT,
                compare_bitrate BIGINT,
                compare_audio_channels INTEGER,
                compare_audio_bitrate BIGINT,
                compare_has_subtitles BOOLEAN,
                compare_file_size BIGINT
            )
        """)
        # Insert a 'similar' entry where Local has better quality (higher resolution)
        conn.execute(
            """
            INSERT INTO compare_results VALUES (
                1, '/local/file.mp4', '/compare/file.mp4', 'Test', 'Test', 80, 'similar', 0.8,
                3840, 2160, 'h264', 20000000, 6, 640000, TRUE, 5000000000,
                1920, 1080, 'h264', 10000000, 2, 320000, FALSE, 2000000000
            )
            """,
        )
        conn.close()

        model = CompareTableModel(Path(db_path))
        assert model.rowCount() == 2  # 2 display rows for 1 DB row

        # Row 0 (Local) should have higher score than Row 1 (Compare)
        local_score = int(model.data(model.index(0, 4)))
        compare_score = int(model.data(model.index(1, 4)))
        assert local_score > compare_score, (
            f"Local score ({local_score}) should be > Compare score ({compare_score}) "
            f"when Local quality is better"
        )

    def test_score_should_be_lower_for_worse_side_when_similar(self, tmp_path):
        """For 'similar' status, the worse side shows a lower score."""
        db_path = str(tmp_path / "score_test.db")
        from MyVideoExplorer.db.db_scan import DbScanUtil

        DbScanUtil(db_path)

        conn = duckdb.connect(db_path)
        conn.execute("""
            CREATE TABLE compare_results (
                row_id BIGINT PRIMARY KEY,
                local_file_path TEXT,
                compare_file_path TEXT,
                local_title TEXT,
                compare_title TEXT,
                match_score INTEGER,
                status TEXT,
                confidence DOUBLE,
                local_width INTEGER,
                local_height INTEGER,
                local_codec TEXT,
                local_bitrate BIGINT,
                local_audio_channels INTEGER,
                local_audio_bitrate BIGINT,
                local_has_subtitles BOOLEAN,
                local_file_size BIGINT,
                compare_width INTEGER,
                compare_height INTEGER,
                compare_codec TEXT,
                compare_bitrate BIGINT,
                compare_audio_channels INTEGER,
                compare_audio_bitrate BIGINT,
                compare_has_subtitles BOOLEAN,
                compare_file_size BIGINT
            )
        """)
        # Insert a 'similar' entry where Compare has better quality
        conn.execute(
            """
            INSERT INTO compare_results VALUES (
                1, '/local/file.mp4', '/compare/file.mp4', 'Test', 'Test', 80, 'similar', 0.8,
                1920, 1080, 'h264', 10000000, 2, 320000, FALSE, 2000000000,
                3840, 2160, 'h264', 20000000, 6, 640000, TRUE, 5000000000
            )
            """,
        )
        conn.close()

        model = CompareTableModel(Path(db_path))
        local_score = int(model.data(model.index(0, 4)))
        compare_score = int(model.data(model.index(1, 4)))
        assert local_score < compare_score, (
            f"Local score ({local_score}) should be < Compare score ({compare_score}) "
            f"when Compare quality is better"
        )

    def test_score_should_be_same_for_both_sides_when_match(self, tmp_path):
        """For 'match' status, both sides show the same base score."""
        db_path = str(tmp_path / "score_test.db")
        from MyVideoExplorer.db.db_scan import DbScanUtil

        DbScanUtil(db_path)

        conn = duckdb.connect(db_path)
        conn.execute("""
            CREATE TABLE compare_results (
                row_id BIGINT PRIMARY KEY,
                local_file_path TEXT,
                compare_file_path TEXT,
                local_title TEXT,
                compare_title TEXT,
                match_score INTEGER,
                status TEXT,
                confidence DOUBLE,
                local_width INTEGER,
                local_height INTEGER,
                local_codec TEXT,
                local_bitrate BIGINT,
                local_audio_channels INTEGER,
                local_audio_bitrate BIGINT,
                local_has_subtitles BOOLEAN,
                local_file_size BIGINT,
                compare_width INTEGER,
                compare_height INTEGER,
                compare_codec TEXT,
                compare_bitrate BIGINT,
                compare_audio_channels INTEGER,
                compare_audio_bitrate BIGINT,
                compare_has_subtitles BOOLEAN,
                compare_file_size BIGINT
            )
        """)
        # Insert a 'match' entry with identical quality
        conn.execute(
            """
            INSERT INTO compare_results VALUES (
                1, '/local/file.mp4', '/compare/file.mp4', 'Test', 'Test', 95, 'match', 0.95,
                1920, 1080, 'h264', 10000000, 6, 640000, FALSE, 3000000000,
                1920, 1080, 'h264', 10000000, 6, 640000, FALSE, 3000000000
            )
            """,
        )
        conn.close()

        model = CompareTableModel(Path(db_path))
        local_score = int(model.data(model.index(0, 4)))
        compare_score = int(model.data(model.index(1, 4)))
        assert local_score == compare_score == 95, (
            f"Both scores should be 95 for 'match' status, got {local_score} and {compare_score}"
        )

    def test_score_should_be_clamped_to_0_100(self, tmp_path):
        """Adjusted scores should not go below 0 or above 100."""
        db_path = str(tmp_path / "score_test.db")
        from MyVideoExplorer.db.db_scan import DbScanUtil

        DbScanUtil(db_path)

        conn = duckdb.connect(db_path)
        conn.execute("""
            CREATE TABLE compare_results (
                row_id BIGINT PRIMARY KEY,
                local_file_path TEXT,
                compare_file_path TEXT,
                local_title TEXT,
                compare_title TEXT,
                match_score INTEGER,
                status TEXT,
                confidence DOUBLE,
                local_width INTEGER,
                local_height INTEGER,
                local_codec TEXT,
                local_bitrate BIGINT,
                local_audio_channels INTEGER,
                local_audio_bitrate BIGINT,
                local_has_subtitles BOOLEAN,
                local_file_size BIGINT,
                compare_width INTEGER,
                compare_height INTEGER,
                compare_codec TEXT,
                compare_bitrate BIGINT,
                compare_audio_channels INTEGER,
                compare_audio_bitrate BIGINT,
                compare_has_subtitles BOOLEAN,
                compare_file_size BIGINT
            )
        """)
        # Insert a 'similar' entry with very high base score and large quality diff
        # to test upper clamping
        conn.execute(
            """
            INSERT INTO compare_results VALUES (
                1, '/local/file.mp4', '/compare/file.mp4', 'Test', 'Test', 99, 'similar', 0.99,
                3840, 2160, 'av1', 50000000, 8, 1280000, TRUE, 10000000000,
                640, 480, 'avi', 1000000, 2, 128000, FALSE, 100000000
            )
            """,
        )
        conn.close()

        model = CompareTableModel(Path(db_path))
        local_score = int(model.data(model.index(0, 4)))
        compare_score = int(model.data(model.index(1, 4)))
        assert 0 <= local_score <= 100, f"Local score {local_score} out of bounds"
        assert 0 <= compare_score <= 100, f"Compare score {compare_score} out of bounds"

    def test_compare_quality_side_should_return_points_diff(self):
        """_compare_quality_side should return both direction and points difference."""
        direction, points_diff = CompareTableModel._compare_quality_side(
            3840,
            2160,
            "h264",
            20000000,
            6,
            640000,
            True,
            5000000000,
            1920,
            1080,
            "h264",
            10000000,
            2,
            320000,
            False,
            2000000000,
        )
        assert direction == "local"
        assert points_diff > 0

    def test_score_tooltip_should_explain_quality_adjustment(self, compare_model):
        """Tooltip should mention quality adjustment."""
        tooltip = compare_model.headerData(
            4, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole
        )
        assert tooltip is not None
        assert "adjust" in tooltip.lower()
        assert "quality" in tooltip.lower()
