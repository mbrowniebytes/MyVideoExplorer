from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
from PySide6.QtCore import QAbstractTableModel, Qt

# Column definitions for the paired-row comparison table.
# Each comparison pair is displayed as 2 rows: row 0 = local, row 1 = compare.
# Shared columns (Score, Status) show the same value on both rows.
COMPARE_COLUMNS: list[dict[str, Any]] = [
    {"key": "row_number", "title": "#", "width": 40},
    {"key": "title", "title": "Title (Local/Compare)", "width": 250},
    {
        "key": "file_size",
        "title": "Size",
        "width": 100,
        "align": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
    },
    {
        "key": "status",
        "title": "Status",
        "width": 80,
        "align": Qt.AlignmentFlag.AlignCenter,
    },
    {
        "key": "match_score",
        "title": "Score",
        "width": 80,
        "align": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
    },
    {
        "key": "resolution",
        "title": "Resolution",
        "width": 100,
        "align": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
    },
    {
        "key": "codec",
        "title": "Codec",
        "width": 100,
        "align": Qt.AlignmentFlag.AlignCenter,
    },
    {
        "key": "bitrate",
        "title": "Bitrate",
        "width": 100,
        "align": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
    },
    {
        "key": "audio",
        "title": "Audio",
        "width": 120,
        "align": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
    },
    {
        "key": "has_subtitles",
        "title": "Subs",
        "width": 60,
        "align": Qt.AlignmentFlag.AlignCenter,
    },
]

PAGE_SIZE = 100


class CompareTableModel(QAbstractTableModel):
    """Table model for lazy-loading comparison results from DuckDB.

    Each comparison pair is displayed as 2 rows:
    - Row 0 (even): Local data with prefix "Local: "
    - Row 1 (odd): Compare data with prefix "Compare: "
    """

    def __init__(self, compare_db_path: Path, parent: Any = None) -> None:
        """Initialize the table model.

        Args:
            compare_db_path: Path to the compare database with results.
            parent: Qt parent object.
        """
        super().__init__(parent)
        self._compare_db_path = compare_db_path
        self._current_page = 0
        self._total_count = 0
        self._rows: list[tuple] = []
        self._display_rows: list[tuple] = []
        self._sort_column: int = -1
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._status_filters: list[str] = []
        self._search_query: str = ""
        self._show_missing = True
        self._load_page()

    def set_status_filter(self, status: str) -> None:
        """Filter by a single status (legacy compatibility).

        Args:
            status: Status string or empty for all.
        """
        self._status_filters = [status] if status else []
        self._current_page = 0
        self._load_page()

    def set_status_filters(self, statuses: list[str]) -> None:
        """Filter by multiple statuses.

        Args:
            statuses: List of status strings or empty for all.
        """
        self._status_filters = statuses
        self._current_page = 0
        self._load_page()

    def set_search_query(self, query: str) -> None:
        """Set text search query.

        Args:
            query: Search string.
        """
        self._search_query = query
        self._current_page = 0
        self._load_page()

    def set_show_missing(self, show: bool) -> None:
        """Toggle showing missing entries.

        Args:
            show: Whether to show missing entries.
        """
        self._show_missing = show
        self._current_page = 0
        self._load_page()

    def next_page(self) -> bool:
        """Go to the next page.

        Returns:
            True if there is a next page.
        """
        offset = self._current_page * PAGE_SIZE
        if offset + PAGE_SIZE < self._total_count:
            self._current_page += 1
            self._load_page()
            return True
        return False

    def prev_page(self) -> bool:
        """Go to the previous page.

        Returns:
            True if there is a previous page.
        """
        if self._current_page > 0:
            self._current_page -= 1
            self._load_page()
            return True
        return False

    def page_info(self) -> tuple[int, int]:
        """Get current page and total pages.

        Returns:
            Tuple of (current_page, total_pages).
        """
        total_pages = max(1, (self._total_count + PAGE_SIZE - 1) // PAGE_SIZE)
        return self._current_page, total_pages

    def rowCount(self, parent: Any = None) -> int:
        return len(self._display_rows)

    def columnCount(self, parent: Any = None) -> int:
        return len(COMPARE_COLUMNS)

    def data(self, index: Any, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = self._display_rows[index.row()]
        col_key = COMPARE_COLUMNS[index.column()]["key"]

        if role == Qt.ItemDataRole.DisplayRole:
            return row[self._display_column_index(col_key)]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            col_def = COMPARE_COLUMNS[index.column()]
            if "align" in col_def:
                return col_def["align"]
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation != Qt.Orientation.Horizontal:
            return None
        col_def = COMPARE_COLUMNS[section]
        if role == Qt.ItemDataRole.DisplayRole:
            return col_def["title"]
        if role == Qt.ItemDataRole.ToolTipRole and col_def["key"] == "match_score":
            return (
                "Score = fuzzy title match (0-100), adjusted by quality difference "
                "for 'similar' entries. Higher score = better quality. Quality: "
                "resolution > codec (av1>h265>h264>mp4>avi) > file size > bitrate "
                "> audio channels > subtitles."
            )
        return None

    def sort(
        self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder
    ) -> None:
        self.layoutAboutToBeChanged.emit()
        self._sort_column = column
        self._sort_order = order
        self._load_page()
        self.layoutChanged.emit()

    def _build_query(self) -> tuple[str, list[Any]]:
        """Build the SQL query with filters.

        Returns:
            Tuple of (query string, params list).
        """
        query = "SELECT * FROM compare_results WHERE TRUE"
        params: list[Any] = []

        if not self._show_missing:
            query += " AND status != 'missing'"

        if self._status_filters:
            placeholders = ", ".join("?" for _ in self._status_filters)
            query += f" AND status IN ({placeholders})"
            params.extend(self._status_filters)

        if self._search_query:
            search_param = f"%{self._search_query}%"
            # Search by raw text fields
            query += (
                " AND ("
                " local_title ILIKE ?"
                " OR compare_title ILIKE ?"
                " OR local_codec ILIKE ?"
                " OR compare_codec ILIKE ?"
                " OR status ILIKE ?"
                " OR local_file_path ILIKE ?"
                " OR compare_file_path ILIKE ?"
                # Search by formatted file size (GB)
                " OR COALESCE(ROUND(CAST(local_file_size AS DOUBLE) / 1073741824, 2) || ' GB', '') ILIKE ?"
                " OR COALESCE(ROUND(CAST(compare_file_size AS DOUBLE) / 1073741824, 2) || ' GB', '') ILIKE ?"
                # Search by formatted bitrate (Mbps)
                " OR COALESCE(ROUND(CAST(local_bitrate AS DOUBLE) / 1000000, 1) || ' Mbps', '') ILIKE ?"
                " OR COALESCE(ROUND(CAST(compare_bitrate AS DOUBLE) / 1000000, 1) || ' Mbps', '') ILIKE ?"
                # Search by formatted resolution (WxH)
                " OR COALESCE(CAST(local_width AS VARCHAR) || 'x' || CAST(local_height AS VARCHAR), '') ILIKE ?"
                " OR COALESCE(CAST(compare_width AS VARCHAR) || 'x' || CAST(compare_height AS VARCHAR), '') ILIKE ?"
                # Search by formatted audio (channels @ bitrateMbps)
                " OR COALESCE(CAST(local_audio_channels AS VARCHAR) || ' @ ' || ROUND(CAST(local_audio_bitrate AS DOUBLE) / 1000000, 1) || 'Mbps', '') ILIKE ?"
                " OR COALESCE(CAST(compare_audio_channels AS VARCHAR) || ' @ ' || ROUND(CAST(compare_audio_bitrate AS DOUBLE) / 1000000, 1) || 'Mbps', '') ILIKE ?"
                ")"
            )
            params.extend([search_param] * 15)

        if self._sort_column >= 0:
            raw_key = COMPARE_COLUMNS[self._sort_column]["key"]
            assert isinstance(raw_key, str)
            col_key = raw_key
            direction = (
                "ASC" if self._sort_order == Qt.SortOrder.AscendingOrder else "DESC"
            )
            # Map display column keys to DB columns for sorting
            db_col = self._sort_key_to_db_col(col_key)
            if db_col:
                query += f" ORDER BY {db_col} {direction}"
            else:
                query += " ORDER BY match_score DESC"
        else:
            query += " ORDER BY match_score DESC"

        return query, params

    def _sort_key_to_db_col(self, key: str) -> str:
        """Map a display column key to a DB column for sorting.

        For paired rows, sort by the local value of each column.

        Args:
            key: Display column key.

        Returns:
            DB column name or empty string.
        """
        mapping = {
            "row_number": "row_id",
            "title": "local_title",
            "match_score": "match_score",
            "status": "status",
            "resolution": "local_width",
            "codec": "local_codec",
            "bitrate": "local_bitrate",
            "audio": "local_audio_channels",
            "has_subtitles": "local_has_subtitles",
            "file_size": "local_file_size",
        }
        return mapping.get(key, "")

    def _format_resolution(self, width: int | None, height: int | None) -> str:
        """Format resolution as 'WxH' string.

        Args:
            width: Width in pixels.
            height: Height in pixels.

        Returns:
            Formatted resolution string.
        """
        if width and height:
            return f"{width}x{height}"
        return ""

    def _format_bitrate(self, bitrate: int | None) -> str:
        """Format bitrate as Mbps string.

        Args:
            bitrate: Bitrate in bps.

        Returns:
            Formatted bitrate string.
        """
        if bitrate:
            return f"{bitrate / 1_000_000:.1f} Mbps"
        return ""

    def _format_file_size(self, size: int | None) -> str:
        """Format file size always in GB.

        Args:
            size: File size in bytes.

        Returns:
            Formatted file size string in GB, e.g., '1.50 GB'.
        """
        if size is None:
            return ""
        size_gb = size / 1_073_741_824
        return f"{size_gb:.2f} GB"

    def _format_score(
        self,
        match_score: float | None,
        confidence: float | None,
        quality_side: str = "equal",
        points_diff: int = 0,
        status: str = "match",
    ) -> str:
        """Format score adjusted by quality difference for 'similar' entries.

        For 'similar' status, the better side gets a higher score and the worse
        side gets a lower score. For 'match' status, both sides show the same
        base score. The arrow suffix is removed since the score difference
        conveys which is better.

        Args:
            match_score: Match score value.
            confidence: Confidence value (unused, kept for compatibility).
            quality_side: 'local', 'compare', or 'equal' from quality comparison.
            points_diff: Absolute difference in quality points.
            status: Entry status ('match', 'similar', or 'missing').

        Returns:
            Formatted score string, e.g., '87', '79'.
        """
        score = int(match_score if match_score is not None else 0)
        if status == "similar" and points_diff > 0:
            adjustment = points_diff * 5
            if quality_side == "local":
                score = score + adjustment
            elif quality_side == "compare":
                score = score - adjustment
        # Clamp to 0-100
        score = max(0, min(100, score))
        return str(score)

    @staticmethod
    def _compare_quality_side(
        local_width: int | None,
        local_height: int | None,
        local_codec: str | None,
        local_bitrate: int | None,
        local_audio_channels: int | None,
        local_audio_bitrate: int | None,
        local_has_subtitles: bool,
        local_file_size: int | None,
        compare_width: int | None,
        compare_height: int | None,
        compare_codec: str | None,
        compare_bitrate: int | None,
        compare_audio_channels: int | None,
        compare_audio_bitrate: int | None,
        compare_has_subtitles: bool,
        compare_file_size: int | None,
    ) -> tuple[str, int]:
        """Compare quality between local and compare sides to determine which is better.

        Mirrors the service layer's quality comparison logic.

        Returns:
            Tuple of (direction, points_diff) where direction is 'local', 'compare',
            or 'equal', and points_diff is the absolute difference in quality points.
        """
        local_points = 0
        compare_points = 0

        local_res = (local_width or 0) * (local_height or 0)
        compare_res = (compare_width or 0) * (compare_height or 0)
        if local_res > compare_res:
            local_points += 2
        elif compare_res > local_res:
            compare_points += 2

        if local_file_size and compare_file_size:
            ratio = local_file_size / compare_file_size if compare_file_size else 0
            if ratio > 1.25:
                local_points += 1
            elif ratio < 0.75:
                compare_points += 1

        local_codec_rank = CompareTableModel._codec_rank(local_codec)
        compare_codec_rank = CompareTableModel._codec_rank(compare_codec)
        if local_codec_rank > compare_codec_rank:
            local_points += 1
        elif compare_codec_rank > local_codec_rank:
            compare_points += 1

        if local_bitrate and compare_bitrate:
            ratio = local_bitrate / compare_bitrate if compare_bitrate else 0
            if ratio > 1.25:
                local_points += 1
            elif ratio < 0.75:
                compare_points += 1

        if (local_audio_channels or 0) > (compare_audio_channels or 0):
            local_points += 1
        elif (compare_audio_channels or 0) > (local_audio_channels or 0):
            compare_points += 1

        if (local_audio_bitrate or 0) > (compare_audio_bitrate or 0):
            local_points += 1
        elif (compare_audio_bitrate or 0) > (local_audio_bitrate or 0):
            compare_points += 1

        if local_has_subtitles and not compare_has_subtitles:
            local_points += 1
        elif compare_has_subtitles and not local_has_subtitles:
            compare_points += 1

        points_diff = abs(local_points - compare_points)
        if local_points > compare_points:
            return ("local", points_diff)
        if compare_points > local_points:
            return ("compare", points_diff)
        return ("equal", 0)

    @staticmethod
    def _codec_rank(codec: str | None) -> int:
        """Return the ranking of a video codec (higher is better).

        Args:
            codec: Codec name string.

        Returns:
            Rank value.
        """
        if not codec:
            return 0
        codec_lower = codec.lower()
        ranks = {
            "av2": 8,
            "av1": 7,
            "h265": 5,
            "hevc": 5,
            "h264": 4,
            "avc": 4,
            "mkv": 3,
            "mp4": 2,
            "avi": 1,
        }
        for key, rank in ranks.items():
            if key in codec_lower:
                return rank
        return 0

    def _format_audio(self, channels: int | None, bitrate: int | None) -> str:
        """Format audio as 'channels @ bitrateMbps'.

        Args:
            channels: Number of audio channels.
            bitrate: Audio bitrate in bps.

        Returns:
            Formatted audio string, e.g., '2 @ 0.2Mbps'.
        """
        if channels and bitrate:
            return f"{channels} @ {bitrate / 1_000_000:.1f}Mbps"
        if channels:
            return str(channels)
        if bitrate:
            return f"{bitrate / 1_000_000:.1f}Mbps"
        return ""

    def _expand_to_display_rows(
        self, db_rows: list[tuple], row_offset: int
    ) -> list[tuple]:
        """Expand DB rows into paired display rows.

        Each DB row becomes 2 display rows: local (even) and compare (odd).
        Row numbers use L/C suffix: '1L' for Local, '1C' for Compare.
        For 'missing' status, the missing side shows empty values.

        Args:
            db_rows: Raw rows from DuckDB.
            row_offset: Starting row number for numbering.

        Returns:
            List of display rows.
        """
        display_rows = []
        for i, row in enumerate(db_rows):
            row_num = row_offset + i + 1
            status = row[self._db_col("status")]
            match_score = row[self._db_col("match_score")]
            confidence = row[self._db_col("confidence")]

            # Check if local or compare is missing
            local_missing = not row[self._db_col("local_file_path")]
            compare_missing = not row[self._db_col("compare_file_path")]

            # Extract local values from DB row
            local_title = row[self._db_col("local_title")]
            local_width = row[self._db_col("local_width")]
            local_height = row[self._db_col("local_height")]
            local_codec = row[self._db_col("local_codec")]
            local_bitrate = row[self._db_col("local_bitrate")]
            local_audio_ch = row[self._db_col("local_audio_channels")]
            local_audio_br = row[self._db_col("local_audio_bitrate")]
            local_subs = row[self._db_col("local_has_subtitles")]
            local_size = row[self._db_col("local_file_size")]

            # Extract compare values from DB row
            compare_title = row[self._db_col("compare_title")]
            compare_width = row[self._db_col("compare_width")]
            compare_height = row[self._db_col("compare_height")]
            compare_codec = row[self._db_col("compare_codec")]
            compare_bitrate = row[self._db_col("compare_bitrate")]
            compare_audio_ch = row[self._db_col("compare_audio_channels")]
            compare_audio_br = row[self._db_col("compare_audio_bitrate")]
            compare_subs = row[self._db_col("compare_has_subtitles")]
            compare_size = row[self._db_col("compare_file_size")]

            # Determine quality direction and points difference for score adjustment
            quality_side = "equal"
            points_diff = 0
            if not local_missing and not compare_missing:
                quality_side, points_diff = self._compare_quality_side(
                    local_width,
                    local_height,
                    local_codec,
                    local_bitrate,
                    local_audio_ch,
                    local_audio_br,
                    local_subs,
                    local_size,
                    compare_width,
                    compare_height,
                    compare_codec,
                    compare_bitrate,
                    compare_audio_ch,
                    compare_audio_br,
                    compare_subs,
                    compare_size,
                )

            # Row 0: Local data (suffix L)
            # For 'similar' status: if local is better, Local gets higher score;
            # if compare is better, Local gets lower score.
            display_rows.append(
                (
                    f"{row_num}L",  # row_number with L suffix
                    local_title or "",  # title
                    self._format_file_size(local_size)
                    if not local_missing
                    else "",  # file_size
                    status,  # status
                    self._format_score(
                        match_score, confidence, quality_side, points_diff, status
                    ),  # match_score
                    self._format_resolution(local_width, local_height)
                    if not local_missing
                    else "",  # resolution
                    local_codec or "",  # codec
                    self._format_bitrate(local_bitrate)
                    if not local_missing
                    else "",  # bitrate
                    self._format_audio(local_audio_ch, local_audio_br)
                    if not local_missing
                    else "",  # audio
                    "Yes" if local_subs else "",  # has_subtitles
                )
            )

            # Row 1: Compare data (suffix C)
            # For 'similar' status: Compare gets the opposite adjustment of Local.
            # If local is better, Compare gets lower score; if compare is better,
            # Compare gets higher score.
            compare_quality_side = quality_side
            if quality_side == "local":
                compare_quality_side = "compare"
            elif quality_side == "compare":
                compare_quality_side = "local"
            display_rows.append(
                (
                    f"{row_num}C",  # row_number with C suffix
                    compare_title or "",  # title
                    self._format_file_size(compare_size)
                    if not compare_missing
                    else "",  # file_size
                    status,  # status
                    self._format_score(
                        match_score,
                        confidence,
                        compare_quality_side,
                        points_diff,
                        status,
                    ),  # match_score
                    self._format_resolution(compare_width, compare_height)
                    if not compare_missing
                    else "",  # resolution
                    compare_codec or "",  # codec
                    self._format_bitrate(compare_bitrate)
                    if not compare_missing
                    else "",  # bitrate
                    self._format_audio(compare_audio_ch, compare_audio_br)
                    if not compare_missing
                    else "",  # audio
                    "Yes" if compare_subs else "",  # has_subtitles
                )
            )

        return display_rows

    def _db_col(self, col_name: str) -> int:
        """Get the index of a DB column in the result tuple.

        Args:
            col_name: Column name in compare_results table.

        Returns:
            Index in the result tuple.
        """
        db_columns = [
            "row_id",
            "local_file_path",
            "compare_file_path",
            "local_title",
            "compare_title",
            "match_score",
            "status",
            "confidence",
            "local_width",
            "local_height",
            "local_codec",
            "local_bitrate",
            "local_audio_channels",
            "local_audio_bitrate",
            "local_has_subtitles",
            "local_file_size",
            "compare_width",
            "compare_height",
            "compare_codec",
            "compare_bitrate",
            "compare_audio_channels",
            "compare_audio_bitrate",
            "compare_has_subtitles",
            "compare_file_size",
        ]
        return db_columns.index(col_name)

    def _display_column_index(self, key: str) -> int:
        """Get the index of a display column key in the display row tuple.

        Args:
            key: Display column key.

        Returns:
            Index in the display row tuple.
        """
        for i, col in enumerate(COMPARE_COLUMNS):
            if col["key"] == key:
                return i
        return 0

    def _load_page(self) -> None:
        """Load the current page of results."""
        try:
            conn = duckdb.connect(str(self._compare_db_path))
            base_query, params = self._build_query()
            count_query = f"SELECT COUNT(*) FROM ({base_query})"
            count_row = conn.execute(count_query, params).fetchone()
            self._total_count = count_row[0] if count_row else 0

            offset = self._current_page * PAGE_SIZE
            page_params = params + [PAGE_SIZE, offset]
            page_query = base_query + " LIMIT ? OFFSET ?"
            self._rows = conn.execute(page_query, page_params).fetchall()
            conn.close()

            # Expand DB rows into paired display rows
            self._display_rows = self._expand_to_display_rows(self._rows, offset)
            self.layoutChanged.emit()
        except Exception:
            self._rows = []
            self._display_rows = []
            self._total_count = 0
            self.layoutChanged.emit()
