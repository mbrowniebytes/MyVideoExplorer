from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import duckdb


@dataclass
class MediaFileMeta:
    """Metadata for a single media file from DuckDB."""

    file_path: str
    title: str
    year: int | None
    file_size: int | None
    width: int | None
    height: int | None
    codec: str | None
    bitrate: int | None
    audio_channels: int | None
    audio_bitrate: int | None
    has_subtitles: bool


@dataclass
class CompareResult:
    """A single row in the comparison results."""

    local_title: str
    compare_title: str
    local_file_path: str
    compare_file_path: str
    match_score: int
    status: str
    confidence: float
    local_width: int | None
    local_height: int | None
    local_codec: str | None
    local_bitrate: int | None
    local_audio_channels: int | None
    local_audio_bitrate: int | None
    local_has_subtitles: bool
    local_file_size: int | None
    compare_width: int | None
    compare_height: int | None
    compare_codec: str | None
    compare_bitrate: int | None
    compare_audio_channels: int | None
    compare_audio_bitrate: int | None
    compare_has_subtitles: bool
    compare_file_size: int | None


class CompareService:
    """Core service for comparing media files between two DuckDB sources."""

    def __init__(self, base_dir: Path = Path()) -> None:
        """Initialize the compare service.

        Args:
            base_dir: Base directory for importing compare databases.
        """
        self._base_dir = base_dir

    def import_compare_db(self, source_path: Path, media_name: str) -> Path:
        """Copy a source DuckDB file to the compare directory.

        Args:
            source_path: Path to the source DuckDB file.
            media_name: Name used to identify the compare database.

        Returns:
            Path to the copied compare database.
        """
        tmp_dir = self._base_dir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        dest = tmp_dir / f"compare_{media_name}.db"
        shutil.copy2(source_path, dest)
        return dest

    def run_comparison(
        self,
        local_db_path: Path,
        compare_db_path: Path,
    ) -> int:
        """Run comparison between local and compare databases.

        Args:
            local_db_path: Path to the local DuckDB database.
            compare_db_path: Path to the imported compare database.

        Returns:
            Number of comparison results materialized.
        """
        local_files = self._load_media_files(local_db_path)
        compare_files = self._load_media_files(compare_db_path)

        results = self._fuzzy_match_titles(local_files, compare_files)
        self._materialize_results(compare_db_path, results)
        return len(results)

    def _load_media_files(self, db_path: Path) -> list[MediaFileMeta]:
        """Load media files with metadata from a DuckDB database.

        Args:
            db_path: Path to the DuckDB database.

        Returns:
            List of media file metadata.
        """
        conn = duckdb.connect(str(db_path))
        query = """
            SELECT
                mf.file_path,
                mf.title,
                mf.year,
                mf.file_size,
                vf.width,
                vf.height,
                vf.codec_name,
                vf.bitrate,
                af.audio_channels,
                af.audio_bitrate,
                sf.has_subtitles
            FROM media_file mf
            LEFT JOIN (
                SELECT media_file_id, width, height, codec_name, bitrate
                FROM media_file_video
                WHERE stream_index = 0
            ) vf ON mf.id = vf.media_file_id
            LEFT JOIN (
                SELECT media_file_id, MAX(channels) AS audio_channels, MAX(bitrate) AS audio_bitrate
                FROM media_file_audio
                GROUP BY media_file_id
            ) af ON mf.id = af.media_file_id
            LEFT JOIN (
                SELECT media_file_id, TRUE AS has_subtitles
                FROM media_file_subtitle
                GROUP BY media_file_id
            ) sf ON mf.id = sf.media_file_id
        """
        rows = conn.execute(query).fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append(
                MediaFileMeta(
                    file_path=row[0] or "",
                    title=row[1] or "",
                    year=row[2],
                    file_size=row[3],
                    width=row[4],
                    height=row[5],
                    codec=row[6],
                    bitrate=row[7],
                    audio_channels=row[8],
                    audio_bitrate=row[9],
                    has_subtitles=row[10] or False,
                )
            )
        return results

    def _fuzzy_match_titles(
        self, local_files: list[MediaFileMeta], compare_files: list[MediaFileMeta]
    ) -> list[CompareResult]:
        """Match local and compare files using tiered fuzzy title matching.

        Matches are processed in priority order to reduce false positives:
        1. Exact matches (score == 100) — highest priority
        2. High-confidence similar matches (score >= 80)
        3. Lower-confidence matches (score >= 60)
        4. Remaining unmatched files are marked as 'missing'

        Args:
            local_files: List of local media files.
            compare_files: List of compare media files.

        Returns:
            List of comparison results.
        """
        from rapidfuzz import fuzz

        results: list[CompareResult] = []
        matched_local_indices: set[int] = set()
        matched_compare_indices: set[int] = set()

        # Build all possible scores first
        all_scores: list[tuple[int, int, float]] = []
        for li, local in enumerate(local_files):
            for ci, compare in enumerate(compare_files):
                score = fuzz.token_set_ratio(local.title, compare.title)
                if score >= 60:
                    all_scores.append((li, ci, score))

        # Sort by score descending so highest scores are processed first
        all_scores.sort(key=lambda x: x[2], reverse=True)

        # Process in tiers: exact (100), high-confidence (>= 80), then lower (>= 60)
        for li, ci, score in all_scores:
            if li in matched_local_indices or ci in matched_compare_indices:
                continue
            matched_local_indices.add(li)
            matched_compare_indices.add(ci)
            local = local_files[li]
            compare = compare_files[ci]
            status = self._determine_status(score, local, compare)
            confidence = score / 100.0
            results.append(
                CompareResult(
                    local_title=local.title,
                    compare_title=compare.title,
                    local_file_path=local.file_path,
                    compare_file_path=compare.file_path,
                    match_score=int(score),
                    status=status,
                    confidence=confidence,
                    local_width=local.width,
                    local_height=local.height,
                    local_codec=local.codec,
                    local_bitrate=local.bitrate,
                    local_audio_channels=local.audio_channels,
                    local_audio_bitrate=local.audio_bitrate,
                    local_has_subtitles=local.has_subtitles,
                    local_file_size=local.file_size,
                    compare_width=compare.width,
                    compare_height=compare.height,
                    compare_codec=compare.codec,
                    compare_bitrate=compare.bitrate,
                    compare_audio_channels=compare.audio_channels,
                    compare_audio_bitrate=compare.audio_bitrate,
                    compare_has_subtitles=compare.has_subtitles,
                    compare_file_size=compare.file_size,
                )
            )

        # Add unmatched local files as 'missing' entries
        for li, local in enumerate(local_files):
            if li not in matched_local_indices:
                results.append(
                    CompareResult(
                        local_title=local.title,
                        compare_title="",
                        local_file_path=local.file_path,
                        compare_file_path="",
                        match_score=0,
                        status="missing",
                        confidence=0.0,
                        local_width=local.width,
                        local_height=local.height,
                        local_codec=local.codec,
                        local_bitrate=local.bitrate,
                        local_audio_channels=local.audio_channels,
                        local_audio_bitrate=local.audio_bitrate,
                        local_has_subtitles=local.has_subtitles,
                        local_file_size=local.file_size,
                        compare_width=None,
                        compare_height=None,
                        compare_codec=None,
                        compare_bitrate=None,
                        compare_audio_channels=None,
                        compare_audio_bitrate=None,
                        compare_has_subtitles=False,
                        compare_file_size=None,
                    )
                )

        # Add compare files with no local match as 'missing' entries
        for ci, compare in enumerate(compare_files):
            if ci not in matched_compare_indices:
                results.append(
                    CompareResult(
                        local_title="",
                        compare_title=compare.title,
                        local_file_path="",
                        compare_file_path=compare.file_path,
                        match_score=0,
                        status="missing",
                        confidence=0.0,
                        local_width=None,
                        local_height=None,
                        local_codec=None,
                        local_bitrate=None,
                        local_audio_channels=None,
                        local_audio_bitrate=None,
                        local_has_subtitles=False,
                        local_file_size=None,
                        compare_width=compare.width,
                        compare_height=compare.height,
                        compare_codec=compare.codec,
                        compare_bitrate=compare.bitrate,
                        compare_audio_channels=compare.audio_channels,
                        compare_audio_bitrate=compare.audio_bitrate,
                        compare_has_subtitles=compare.has_subtitles,
                        compare_file_size=compare.file_size,
                    )
                )

        return results

    def _determine_status(
        self, score: float, local: MediaFileMeta, compare: MediaFileMeta
    ) -> str:
        """Determine the comparison status based on score and quality.

        'match' requires score >= 80 AND all stats to be identical.
        Any stat difference when score >= 80 yields 'similar'.
        Score < 80 also yields 'similar'.

        Args:
            score: Fuzzy match score (0-100).
            local: Local media file metadata.
            compare: Compare media file metadata.

        Returns:
            Status string: 'match', 'similar', or 'missing'.
        """
        if score >= 80:
            if self._all_stats_match(local, compare):
                return "match"
            # Any stat differs → 'similar', even with high score
            return "similar"
        return "similar"

    @staticmethod
    def _all_stats_match(local: MediaFileMeta, compare: MediaFileMeta) -> bool:
        """Check if all comparable stats between local and compare are identical.

        Args:
            local: Local media file metadata.
            compare: Compare media file metadata.

        Returns:
            True if all stats match exactly.
        """
        return (
            (local.file_size or 0) == (compare.file_size or 0)
            and (local.width or 0) == (compare.width or 0)
            and (local.height or 0) == (compare.height or 0)
            and (local.codec or "").lower() == (compare.codec or "").lower()
            and (local.bitrate or 0) == (compare.bitrate or 0)
            and (local.audio_channels or 0) == (compare.audio_channels or 0)
            and (local.audio_bitrate or 0) == (compare.audio_bitrate or 0)
            and local.has_subtitles == compare.has_subtitles
        )

    def _quality_score(self, local: MediaFileMeta, compare: MediaFileMeta) -> str:
        """Compare quality between local and compare files.

        Args:
            local: Local media file metadata.
            compare: Compare media file metadata.

        Returns:
            Quality comparison: 'better', 'worse', or 'match'.
        """
        local_points = 0
        compare_points = 0

        local_res = (local.width or 0) * (local.height or 0)
        compare_res = (compare.width or 0) * (compare.height or 0)
        if local_res > compare_res:
            local_points += 2
        elif compare_res > local_res:
            compare_points += 2

        if local.file_size and compare.file_size:
            ratio = local.file_size / compare.file_size if compare.file_size else 0
            if ratio > 1.25:
                local_points += 1
            elif ratio < 0.75:
                compare_points += 1

        local_codec_rank = self._codec_rank(local.codec)
        compare_codec_rank = self._codec_rank(compare.codec)
        if local_codec_rank > compare_codec_rank:
            local_points += 1
        elif compare_codec_rank > local_codec_rank:
            compare_points += 1

        if local.bitrate and compare.bitrate:
            ratio = local.bitrate / compare.bitrate if compare.bitrate else 0
            if ratio > 1.25:
                local_points += 1
            elif ratio < 0.75:
                compare_points += 1

        if (local.audio_channels or 0) > (compare.audio_channels or 0):
            local_points += 1
        elif (compare.audio_channels or 0) > (local.audio_channels or 0):
            compare_points += 1

        if (local.audio_bitrate or 0) > (compare.audio_bitrate or 0):
            local_points += 1
        elif (compare.audio_bitrate or 0) > (local.audio_bitrate or 0):
            compare_points += 1

        if local.has_subtitles and not compare.has_subtitles:
            local_points += 1
        elif compare.has_subtitles and not local.has_subtitles:
            compare_points += 1

        if local_points > compare_points:
            return "better"
        if compare_points > local_points:
            return "worse"
        return "match"

    def _compare_quality_side(
        self, local: MediaFileMeta, compare: MediaFileMeta
    ) -> str:
        """Compare quality between local and compare files to determine which side is better.

        Used by the model layer to append arrow direction to the Score display.

        Args:
            local: Local media file metadata.
            compare: Compare media file metadata.

        Returns:
            'local' if Local quality is better, 'compare' if Compare is better, 'equal' if tied.
        """
        local_points = 0
        compare_points = 0

        local_res = (local.width or 0) * (local.height or 0)
        compare_res = (compare.width or 0) * (compare.height or 0)
        if local_res > compare_res:
            local_points += 2
        elif compare_res > local_res:
            compare_points += 2

        if local.file_size and compare.file_size:
            ratio = local.file_size / compare.file_size if compare.file_size else 0
            if ratio > 1.25:
                local_points += 1
            elif ratio < 0.75:
                compare_points += 1

        local_codec_rank = self._codec_rank(local.codec)
        compare_codec_rank = self._codec_rank(compare.codec)
        if local_codec_rank > compare_codec_rank:
            local_points += 1
        elif compare_codec_rank > local_codec_rank:
            compare_points += 1

        if local.bitrate and compare.bitrate:
            ratio = local.bitrate / compare.bitrate if compare.bitrate else 0
            if ratio > 1.25:
                local_points += 1
            elif ratio < 0.75:
                compare_points += 1

        if (local.audio_channels or 0) > (compare.audio_channels or 0):
            local_points += 1
        elif (compare.audio_channels or 0) > (local.audio_channels or 0):
            compare_points += 1

        if (local.audio_bitrate or 0) > (compare.audio_bitrate or 0):
            local_points += 1
        elif (compare.audio_bitrate or 0) > (local.audio_bitrate or 0):
            compare_points += 1

        if local.has_subtitles and not compare.has_subtitles:
            local_points += 1
        elif compare.has_subtitles and not local.has_subtitles:
            compare_points += 1

        if local_points > compare_points:
            return "local"
        if compare_points > local_points:
            return "compare"
        return "equal"

    @staticmethod
    def _codec_rank(codec: str | None) -> int:
        """Return the ranking of a video codec.

        Args:
            codec: Codec name string.

        Returns:
            Rank value (higher is better).
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

    def _materialize_results(
        self, compare_db_path: Path, results: list[CompareResult]
    ) -> None:
        """Store comparison results in the compare database.

        Args:
            compare_db_path: Path to the compare database.
            results: List of comparison results.
        """
        conn = duckdb.connect(str(compare_db_path))
        conn.execute("DROP TABLE IF EXISTS compare_results")
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
        for i, r in enumerate(results):
            conn.execute(
                """
                INSERT INTO compare_results VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
            """,
                [
                    i,
                    r.local_file_path,
                    r.compare_file_path,
                    r.local_title,
                    r.compare_title,
                    r.match_score,
                    r.status,
                    r.confidence,
                    r.local_width,
                    r.local_height,
                    r.local_codec,
                    r.local_bitrate,
                    r.local_audio_channels,
                    r.local_audio_bitrate,
                    r.local_has_subtitles,
                    r.local_file_size,
                    r.compare_width,
                    r.compare_height,
                    r.compare_codec,
                    r.compare_bitrate,
                    r.compare_audio_channels,
                    r.compare_audio_bitrate,
                    r.compare_has_subtitles,
                    r.compare_file_size,
                ],
            )
        conn.close()
