"""Fixtures for creating test databases with media files and ffprobe metadata."""

from __future__ import annotations

import duckdb
import pytest

from MyVideoExplorer.db.db_scan import DbScanUtil


def create_test_db(
    db_path: str,
    media_files: list[dict] | None = None,
    video_meta: list[dict] | None = None,
    audio_meta: list[dict] | None = None,
    subtitle_meta: list[dict] | None = None,
) -> str:
    """Create a test database with media files and optional ffprobe metadata.

    Args:
        db_path: Path to the database file.
        media_files: List of media file dicts with file_path, title, year, etc.
        video_meta: List of video metadata dicts with media_file_id, width, height, etc.
        audio_meta: List of audio metadata dicts with media_file_id, channels, etc.
        subtitle_meta: List of subtitle metadata dicts with media_file_id, format, etc.

    Returns:
        The database path.
    """
    db_util = DbScanUtil(db_path)

    if media_files:
        db_util.save_media(media_files, "/test/media")

    conn = duckdb.connect(db_path)
    try:
        if video_meta:
            for v in video_meta:
                conn.execute(
                    """
                    INSERT INTO media_file_video (
                        id, media_file_id, stream_index, width, height,
                        codec_name, bitrate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        v.get("id", 0),
                        v["media_file_id"],
                        v.get("stream_index", 0),
                        v.get("width"),
                        v.get("height"),
                        v.get("codec_name"),
                        v.get("bitrate"),
                    ],
                )

        if audio_meta:
            for a in audio_meta:
                conn.execute(
                    """
                    INSERT INTO media_file_audio (
                        id, media_file_id, stream_index, codec_name,
                        channels, bitrate
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        a.get("id", 0),
                        a["media_file_id"],
                        a.get("stream_index", 0),
                        a.get("codec_name"),
                        a.get("channels"),
                        a.get("bitrate"),
                    ],
                )

        if subtitle_meta:
            for s in subtitle_meta:
                conn.execute(
                    """
                    INSERT INTO media_file_subtitle (
                        id, media_file_id, stream_index, format, lang
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        s.get("id", 0),
                        s["media_file_id"],
                        s.get("stream_index", 0),
                        s.get("format"),
                        s.get("lang"),
                    ],
                )
    finally:
        conn.close()

    return db_path


def get_media_file_ids(db_path: str) -> dict[str, int]:
    """Get a mapping of file_path to media_file_id.

    Args:
        db_path: Path to the database.

    Returns:
        Dict mapping file_path to id.
    """
    conn = duckdb.connect(db_path)
    rows = conn.execute("SELECT id, file_path FROM media_file").fetchall()
    conn.close()
    return {row[1]: row[0] for row in rows}


@pytest.fixture
def local_test_db(tmp_path):
    """Create a local test database with sample media files."""
    db_path = str(tmp_path / "local_test.db")

    media_files = [
        {
            "file_path": "/test/media/The Dark Knight.mp4",
            "metadata": {
                "title": "The Dark Knight",
                "year": 2008,
            },
        },
        {
            "file_path": "/test/media/Inception.mkv",
            "metadata": {
                "title": "Inception",
                "year": 2010,
            },
        },
        {
            "file_path": "/test/media/The Matrix.mp4",
            "metadata": {
                "title": "The Matrix",
                "year": 1999,
            },
        },
        {
            "file_path": "/test/media/Interstellar.mkv",
            "metadata": {
                "title": "Interstellar",
                "year": 2014,
            },
        },
        {
            "file_path": "/test/media/Pulp Fiction.mp4",
            "metadata": {
                "title": "Pulp Fiction",
                "year": 1994,
            },
        },
    ]

    db_util = DbScanUtil(db_path)
    db_util.save_media(media_files, "/test/media")

    file_ids = get_media_file_ids(db_path)

    conn = duckdb.connect(db_path)
    try:
        # Video metadata
        video_meta = [
            {
                "id": 1,
                "media_file_id": file_ids["/test/media/The Dark Knight.mp4"],
                "stream_index": 0,
                "width": 1920,
                "height": 1080,
                "codec_name": "h264",
                "bitrate": 8000000,
            },
            {
                "id": 2,
                "media_file_id": file_ids["/test/media/Inception.mkv"],
                "stream_index": 0,
                "width": 3840,
                "height": 2160,
                "codec_name": "h265",
                "bitrate": 20000000,
            },
            {
                "id": 3,
                "media_file_id": file_ids["/test/media/The Matrix.mp4"],
                "stream_index": 0,
                "width": 1920,
                "height": 1080,
                "codec_name": "h264",
                "bitrate": 6000000,
            },
            {
                "id": 4,
                "media_file_id": file_ids["/test/media/Interstellar.mkv"],
                "stream_index": 0,
                "width": 3840,
                "height": 2160,
                "codec_name": "av1",
                "bitrate": 25000000,
            },
            {
                "id": 5,
                "media_file_id": file_ids["/test/media/Pulp Fiction.mp4"],
                "stream_index": 0,
                "width": 1920,
                "height": 1080,
                "codec_name": "h264",
                "bitrate": 5000000,
            },
        ]

        # Audio metadata
        audio_meta = [
            {
                "id": 101,
                "media_file_id": file_ids["/test/media/The Dark Knight.mp4"],
                "stream_index": 1,
                "codec_name": "aac",
                "channels": 6,
                "bitrate": 640000,
            },
            {
                "id": 102,
                "media_file_id": file_ids["/test/media/Inception.mkv"],
                "stream_index": 1,
                "codec_name": "truehd",
                "channels": 8,
                "bitrate": 3840000,
            },
            {
                "id": 103,
                "media_file_id": file_ids["/test/media/The Matrix.mp4"],
                "stream_index": 1,
                "codec_name": "aac",
                "channels": 2,
                "bitrate": 256000,
            },
            {
                "id": 104,
                "media_file_id": file_ids["/test/media/Interstellar.mkv"],
                "stream_index": 1,
                "codec_name": "truehd",
                "channels": 8,
                "bitrate": 4800000,
            },
            {
                "id": 105,
                "media_file_id": file_ids["/test/media/Pulp Fiction.mp4"],
                "stream_index": 1,
                "codec_name": "aac",
                "channels": 2,
                "bitrate": 192000,
            },
        ]

        # Subtitle metadata (only for some files)
        subtitle_meta = [
            {
                "id": 201,
                "media_file_id": file_ids["/test/media/Inception.mkv"],
                "stream_index": 2,
                "format": "srt",
                "lang": "eng",
            },
            {
                "id": 202,
                "media_file_id": file_ids["/test/media/Interstellar.mkv"],
                "stream_index": 2,
                "format": "srt",
                "lang": "eng",
            },
        ]

        for v in video_meta:
            conn.execute(
                """
                INSERT INTO media_file_video (
                    id, media_file_id, stream_index, width, height,
                    codec_name, bitrate
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    v["id"],
                    v["media_file_id"],
                    v["stream_index"],
                    v["width"],
                    v["height"],
                    v["codec_name"],
                    v["bitrate"],
                ],
            )

        for a in audio_meta:
            conn.execute(
                """
                INSERT INTO media_file_audio (
                    id, media_file_id, stream_index, codec_name,
                    channels, bitrate
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    a["id"],
                    a["media_file_id"],
                    a["stream_index"],
                    a["codec_name"],
                    a["channels"],
                    a["bitrate"],
                ],
            )

        for s in subtitle_meta:
            conn.execute(
                """
                INSERT INTO media_file_subtitle (
                    id, media_file_id, stream_index, format, lang
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    s["id"],
                    s["media_file_id"],
                    s["stream_index"],
                    s["format"],
                    s["lang"],
                ],
            )
    finally:
        conn.close()

    return db_path


@pytest.fixture
def compare_test_db(tmp_path):
    """Create a compare test database with slightly different media files."""
    db_path = str(tmp_path / "compare_test.db")

    media_files = [
        {
            "file_path": "/compare/media/Dark Knight The.mp4",
            "metadata": {
                "title": "Dark Knight The",
                "year": 2008,
            },
        },
        {
            "file_path": "/compare/media/Inception 2010.mkv",
            "metadata": {
                "title": "Inception 2010",
                "year": 2010,
            },
        },
        {
            "file_path": "/compare/media/The Matrix Reloaded.mp4",
            "metadata": {
                "title": "The Matrix Reloaded",
                "year": 2003,
            },
        },
        {
            "file_path": "/compare/media/Blade Runner 2049.mkv",
            "metadata": {
                "title": "Blade Runner 2049",
                "year": 2017,
            },
        },
        {
            "file_path": "/compare/media/Pulp Fiction 1994.mp4",
            "metadata": {
                "title": "Pulp Fiction 1994",
                "year": 1994,
            },
        },
    ]

    db_util = DbScanUtil(db_path)
    db_util.save_media(media_files, "/compare/media")

    file_ids = get_media_file_ids(db_path)

    conn = duckdb.connect(db_path)
    try:
        # Video metadata - different quality levels
        video_meta = [
            {
                "id": 1,
                "media_file_id": file_ids["/compare/media/Dark Knight The.mp4"],
                "stream_index": 0,
                "width": 1920,
                "height": 1080,
                "codec_name": "h265",
                "bitrate": 10000000,
            },
            {
                "id": 2,
                "media_file_id": file_ids["/compare/media/Inception 2010.mkv"],
                "stream_index": 0,
                "width": 1920,
                "height": 1080,
                "codec_name": "h264",
                "bitrate": 15000000,
            },
            {
                "id": 3,
                "media_file_id": file_ids["/compare/media/The Matrix Reloaded.mp4"],
                "stream_index": 0,
                "width": 1280,
                "height": 720,
                "codec_name": "h264",
                "bitrate": 4000000,
            },
            {
                "id": 4,
                "media_file_id": file_ids["/compare/media/Blade Runner 2049.mkv"],
                "stream_index": 0,
                "width": 3840,
                "height": 2160,
                "codec_name": "av1",
                "bitrate": 30000000,
            },
            {
                "id": 5,
                "media_file_id": file_ids["/compare/media/Pulp Fiction 1994.mp4"],
                "stream_index": 0,
                "width": 1920,
                "height": 1080,
                "codec_name": "h264",
                "bitrate": 5000000,
            },
        ]

        # Audio metadata
        audio_meta = [
            {
                "id": 101,
                "media_file_id": file_ids["/compare/media/Dark Knight The.mp4"],
                "stream_index": 1,
                "codec_name": "aac",
                "channels": 6,
                "bitrate": 640000,
            },
            {
                "id": 102,
                "media_file_id": file_ids["/compare/media/Inception 2010.mkv"],
                "stream_index": 1,
                "codec_name": "aac",
                "channels": 6,
                "bitrate": 640000,
            },
            {
                "id": 103,
                "media_file_id": file_ids["/compare/media/The Matrix Reloaded.mp4"],
                "stream_index": 1,
                "codec_name": "aac",
                "channels": 2,
                "bitrate": 192000,
            },
            {
                "id": 104,
                "media_file_id": file_ids["/compare/media/Blade Runner 2049.mkv"],
                "stream_index": 1,
                "codec_name": "truehd",
                "channels": 8,
                "bitrate": 4800000,
            },
            {
                "id": 105,
                "media_file_id": file_ids["/compare/media/Pulp Fiction 1994.mp4"],
                "stream_index": 1,
                "codec_name": "aac",
                "channels": 2,
                "bitrate": 192000,
            },
        ]

        # Subtitle metadata
        subtitle_meta = [
            {
                "id": 201,
                "media_file_id": file_ids["/compare/media/Dark Knight The.mp4"],
                "stream_index": 2,
                "format": "srt",
                "lang": "eng",
            },
            {
                "id": 202,
                "media_file_id": file_ids["/compare/media/Blade Runner 2049.mkv"],
                "stream_index": 2,
                "format": "srt",
                "lang": "eng",
            },
        ]

        for v in video_meta:
            conn.execute(
                """
                INSERT INTO media_file_video (
                    id, media_file_id, stream_index, width, height,
                    codec_name, bitrate
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    v["id"],
                    v["media_file_id"],
                    v["stream_index"],
                    v["width"],
                    v["height"],
                    v["codec_name"],
                    v["bitrate"],
                ],
            )

        for a in audio_meta:
            conn.execute(
                """
                INSERT INTO media_file_audio (
                    id, media_file_id, stream_index, codec_name,
                    channels, bitrate
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    a["id"],
                    a["media_file_id"],
                    a["stream_index"],
                    a["codec_name"],
                    a["channels"],
                    a["bitrate"],
                ],
            )

        for s in subtitle_meta:
            conn.execute(
                """
                INSERT INTO media_file_subtitle (
                    id, media_file_id, stream_index, format, lang
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    s["id"],
                    s["media_file_id"],
                    s["stream_index"],
                    s["format"],
                    s["lang"],
                ],
            )
    finally:
        conn.close()

    return db_path
