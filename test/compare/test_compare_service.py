"""Tests for CompareService — fuzzy matching, quality scoring, and comparison."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import duckdb
import pytest

from MyVideoExplorer.compare.compare_service import (
    CompareService,
    MediaFileMeta,
)


class TestCompareServiceCodecRank:
    """Test _codec_rank static method."""

    def test_codec_rank_av2_should_return_highest(self):
        assert CompareService._codec_rank("av2") == 8
        assert CompareService._codec_rank("AV2") == 8

    def test_codec_rank_av1_should_return_7(self):
        assert CompareService._codec_rank("av1") == 7

    def test_codec_rank_h265_hevc_should_return_5(self):
        assert CompareService._codec_rank("h265") == 5
        assert CompareService._codec_rank("hevc") == 5

    def test_codec_rank_h264_avc_should_return_4(self):
        assert CompareService._codec_rank("h264") == 4
        assert CompareService._codec_rank("avc") == 4

    def test_codec_rank_mkv_should_return_3(self):
        assert CompareService._codec_rank("mkv") == 3

    def test_codec_rank_mp4_should_return_2(self):
        assert CompareService._codec_rank("mp4") == 2

    def test_codec_rank_avi_should_return_1(self):
        assert CompareService._codec_rank("avi") == 1

    def test_codec_rank_unknown_should_return_0(self):
        assert CompareService._codec_rank("vp9") == 0
        assert CompareService._codec_rank(None) == 0
        assert CompareService._codec_rank("") == 0


class TestCompareServiceQualityScore:
    """Test _quality_score method."""

    @pytest.fixture
    def service(self, tmp_path):
        return CompareService()

    def test_quality_score_higher_resolution_should_be_better(self, service):
        local = MediaFileMeta(
            file_path="/local/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=3840,
            height=2160,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        compare = MediaFileMeta(
            file_path="/compare/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        assert service._quality_score(local, compare) == "better"

    def test_quality_score_lower_resolution_should_be_worse(self, service):
        local = MediaFileMeta(
            file_path="/local/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        compare = MediaFileMeta(
            file_path="/compare/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=3840,
            height=2160,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        assert service._quality_score(local, compare) == "worse"

    def test_quality_score_larger_file_size_should_be_better(self, service):
        local = MediaFileMeta(
            file_path="/local/movie.mp4",
            title="Movie",
            year=2020,
            file_size=2000000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        compare = MediaFileMeta(
            file_path="/compare/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        assert service._quality_score(local, compare) == "better"

    def test_quality_score_small_file_size_diff_should_be_match(self, service):
        local = MediaFileMeta(
            file_path="/local/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1100000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        compare = MediaFileMeta(
            file_path="/compare/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        # 10% difference is within threshold, should be match
        assert service._quality_score(local, compare) == "match"

    def test_quality_score_better_codec_should_be_better(self, service):
        local = MediaFileMeta(
            file_path="/local/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=1920,
            height=1080,
            codec="h265",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        compare = MediaFileMeta(
            file_path="/compare/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        assert service._quality_score(local, compare) == "better"

    def test_quality_score_more_audio_channels_should_be_better(self, service):
        local = MediaFileMeta(
            file_path="/local/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=8,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        compare = MediaFileMeta(
            file_path="/compare/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        assert service._quality_score(local, compare) == "better"

    def test_quality_score_subtitles_should_be_better(self, service):
        local = MediaFileMeta(
            file_path="/local/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=True,
        )
        compare = MediaFileMeta(
            file_path="/compare/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        assert service._quality_score(local, compare) == "better"

    def test_quality_score_identical_should_be_match(self, service):
        local = MediaFileMeta(
            file_path="/local/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        compare = MediaFileMeta(
            file_path="/compare/movie.mp4",
            title="Movie",
            year=2020,
            file_size=1000000,
            width=1920,
            height=1080,
            codec="h264",
            bitrate=10000000,
            audio_channels=6,
            audio_bitrate=640000,
            has_subtitles=False,
        )
        assert service._quality_score(local, compare) == "match"


class TestCompareServiceDetermineStatus:
    """Test _determine_status method with stricter match logic."""

    @pytest.fixture
    def service(self, tmp_path):
        return CompareService()

    def _identical_files(self):
        """Return two identical MediaFileMeta instances."""
        return (
            MediaFileMeta(
                file_path="/local/movie.mp4",
                title="Movie",
                year=2020,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            ),
            MediaFileMeta(
                file_path="/compare/movie.mp4",
                title="Movie",
                year=2020,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            ),
        )

    def test_determine_status_all_stats_match_should_be_match(self, service):
        """Score >= 80 with all stats identical should return 'match'."""
        local, compare = self._identical_files()
        assert service._determine_status(100, local, compare) == "match"

    def test_determine_status_file_size_differs_should_be_similar(self, service):
        """Score >= 80 with file size differing should return 'similar'."""
        local, compare = self._identical_files()
        compare = replace(compare, file_size=2000000)
        assert service._determine_status(100, local, compare) == "similar"

    def test_determine_status_codec_differs_should_be_similar(self, service):
        """Score >= 80 with codec differing should return 'similar'."""
        local, compare = self._identical_files()
        compare = replace(compare, codec="h265")
        assert service._determine_status(100, local, compare) == "similar"

    def test_determine_status_resolution_differs_should_be_similar(self, service):
        """Score >= 80 with resolution differing should return 'similar'."""
        local, compare = self._identical_files()
        compare = replace(compare, width=3840, height=2160)
        assert service._determine_status(100, local, compare) == "similar"

    def test_determine_status_bitrate_differs_should_be_similar(self, service):
        """Score >= 80 with bitrate differing should return 'similar'."""
        local, compare = self._identical_files()
        compare = replace(compare, bitrate=20000000)
        assert service._determine_status(100, local, compare) == "similar"

    def test_determine_status_audio_differs_should_be_similar(self, service):
        """Score >= 80 with audio channels differing should return 'similar'."""
        local, compare = self._identical_files()
        compare = replace(compare, audio_channels=8)
        assert service._determine_status(100, local, compare) == "similar"

    def test_determine_status_subtitles_differs_should_be_similar(self, service):
        """Score >= 80 with subtitles differing should return 'similar'."""
        local, compare = self._identical_files()
        compare = replace(compare, has_subtitles=True)
        assert service._determine_status(100, local, compare) == "similar"

    def test_determine_status_low_score_should_be_similar(self, service):
        """Score < 80 should always return 'similar'."""
        local, compare = self._identical_files()
        assert service._determine_status(50, local, compare) == "similar"


class TestCompareServiceFuzzyMatch:
    """Test _fuzzy_match_titles method."""

    @pytest.fixture
    def service(self, tmp_path):
        return CompareService()

    def test_fuzzy_match_exact_titles_should_match(self, service):
        local = [
            MediaFileMeta(
                file_path="/local/movie.mp4",
                title="The Dark Knight",
                year=2008,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            )
        ]
        compare = [
            MediaFileMeta(
                file_path="/compare/movie.mp4",
                title="The Dark Knight",
                year=2008,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            )
        ]
        results = service._fuzzy_match_titles(local, compare)
        assert len(results) == 1
        assert results[0].match_score == 100
        assert results[0].status == "match"

    def test_fuzzy_match_reordered_words_should_match(self, service):
        local = [
            MediaFileMeta(
                file_path="/local/movie.mp4",
                title="The Dark Knight",
                year=2008,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            )
        ]
        compare = [
            MediaFileMeta(
                file_path="/compare/movie.mp4",
                title="Dark Knight The",
                year=2008,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            )
        ]
        results = service._fuzzy_match_titles(local, compare)
        assert len(results) == 1
        assert results[0].match_score >= 80
        assert results[0].status in ("match", "better", "worse")

    def test_fuzzy_match_similar_titles_should_be_similar(self, service):
        local = [
            MediaFileMeta(
                file_path="/local/movie.mp4",
                title="Inception",
                year=2010,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            )
        ]
        compare = [
            MediaFileMeta(
                file_path="/compare/movie.mp4",
                title="Inception 2010",
                year=2010,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            )
        ]
        results = service._fuzzy_match_titles(local, compare)
        assert len(results) == 1
        # Inception vs Inception 2010 should match with high score
        assert results[0].match_score >= 60
        assert results[0].status in ("similar", "match", "better", "worse")

    def test_fuzzy_match_no_match_should_be_missing(self, service):
        local = [
            MediaFileMeta(
                file_path="/local/movie.mp4",
                title="Inception",
                year=2010,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            )
        ]
        compare = [
            MediaFileMeta(
                file_path="/compare/movie.mp4",
                title="Blade Runner 2049",
                year=2017,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            )
        ]
        results = service._fuzzy_match_titles(local, compare)
        # Both sides unmatched: 1 missing for local, 1 missing for compare
        assert len(results) == 2
        assert all(r.status == "missing" for r in results)
        assert all(r.match_score == 0 for r in results)

    def test_fuzzy_match_empty_compare_should_all_be_missing(self, service):
        local = [
            MediaFileMeta(
                file_path="/local/movie.mp4",
                title="Movie",
                year=2020,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            )
        ]
        results = service._fuzzy_match_titles(local, [])
        assert len(results) == 1
        assert results[0].status == "missing"

    def test_fuzzy_match_empty_local_should_be_missing(self, service):
        """Compare files with no local match should produce 'missing' entries."""
        compare = [
            MediaFileMeta(
                file_path="/compare/movie.mp4",
                title="Movie",
                year=2020,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            )
        ]
        results = service._fuzzy_match_titles([], compare)
        assert len(results) == 1
        assert results[0].status == "missing"
        assert results[0].local_file_path == ""
        assert results[0].compare_file_path == "/compare/movie.mp4"

    def test_fuzzy_match_unmatched_compare_should_be_missing(self, service):
        """Compare file with no local match should produce 'missing' entry."""
        local = [
            MediaFileMeta(
                file_path="/local/movie.mp4",
                title="The Dark Knight",
                year=2008,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            )
        ]
        compare = [
            MediaFileMeta(
                file_path="/compare/matched.mp4",
                title="The Dark Knight",
                year=2008,
                file_size=1000000,
                width=1920,
                height=1080,
                codec="h264",
                bitrate=10000000,
                audio_channels=6,
                audio_bitrate=640000,
                has_subtitles=False,
            ),
            MediaFileMeta(
                file_path="/compare/unmatched.mp4",
                title="Some Other Movie",
                year=2020,
                file_size=2000000,
                width=3840,
                height=2160,
                codec="h265",
                bitrate=20000000,
                audio_channels=8,
                audio_bitrate=1280000,
                has_subtitles=True,
            ),
        ]
        results = service._fuzzy_match_titles(local, compare)
        # Should have 2 results: 1 match + 1 missing (unmatched compare)
        assert len(results) == 2
        statuses = [r.status for r in results]
        assert "match" in statuses
        assert "missing" in statuses
        missing_result = next(r for r in results if r.status == "missing")
        assert missing_result.local_file_path == ""
        assert missing_result.compare_file_path == "/compare/unmatched.mp4"


class TestCompareServiceImportDb:
    """Test import_compare_db method."""

    def test_import_compare_db_should_copy_file(self, tmp_path):
        source = tmp_path / "source.db"
        source.write_text("test db content")

        service = CompareService(tmp_path)
        dest = service.import_compare_db(source, "test")

        assert dest.name == "compare_test.db"
        assert dest.exists()
        assert str(tmp_path) in str(dest.parent)
        # Cleanup
        dest.unlink()


class TestCompareServiceRunComparison:
    """Test run_comparison end-to-end with test databases."""

    def test_run_comparison_should_match_titles_and_materialize(
        self, local_test_db, compare_test_db
    ):
        service = CompareService()
        count = service.run_comparison(Path(local_test_db), Path(compare_test_db))

        assert count > 0

        conn = duckdb.connect(compare_test_db)
        rows = conn.execute("SELECT * FROM compare_results ORDER BY row_id").fetchall()
        conn.close()

        assert len(rows) == count

    def test_run_comparison_should_include_missing_entries(
        self, local_test_db, compare_test_db
    ):
        service = CompareService()
        service.run_comparison(Path(local_test_db), Path(compare_test_db))

        conn = duckdb.connect(compare_test_db)
        rows = conn.execute(
            "SELECT status FROM compare_results WHERE status = 'missing'"
        ).fetchall()
        conn.close()

        # Interstellar has no match in compare DB
        assert len(rows) >= 1

    def test_run_comparison_should_include_matched_entries(
        self, local_test_db, compare_test_db
    ):
        service = CompareService()
        service.run_comparison(Path(local_test_db), Path(compare_test_db))

        conn = duckdb.connect(compare_test_db)
        # With stricter match logic, matched entries may be 'similar' if stats differ
        rows = conn.execute(
            "SELECT status FROM compare_results WHERE status IN ('match', 'better', 'worse', 'similar')"
        ).fetchall()
        conn.close()

        # Dark Knight, Inception, Pulp Fiction should produce matched entries
        assert len(rows) >= 1

    def test_run_comparison_should_create_compare_results_table(
        self, local_test_db, compare_test_db
    ):
        service = CompareService()
        service.run_comparison(Path(local_test_db), Path(compare_test_db))

        conn = duckdb.connect(compare_test_db)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        conn.close()

        assert "compare_results" in table_names

    def test_run_comparison_empty_dbs_should_return_zero(self, tmp_path):
        local_db = str(tmp_path / "empty_local.db")
        compare_db = str(tmp_path / "empty_compare.db")

        from MyVideoExplorer.db.db_scan import DbScanUtil

        DbScanUtil(local_db)
        DbScanUtil(compare_db)

        service = CompareService()
        count = service.run_comparison(Path(local_db), Path(compare_db))
        assert count == 0
