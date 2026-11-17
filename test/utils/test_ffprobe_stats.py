from __future__ import annotations

import duckdb

from MyVideoExplorer.utils.ffprobe_util import FfprobeUtil


def test_ffprobe_stats_count_only_metadata_tables(tmp_path):
    db_path = str(tmp_path / "media.db")
    util = FfprobeUtil(str(tmp_path), db_path)
    with duckdb.connect(db_path) as con:
        con.execute(
            "INSERT INTO media_file (id, file_path) VALUES (1, 'movie.mkv'), "
            "(2, 'audio-only.mp4')"
        )

    util.save_probe_result(
        1,
        {
            "streams": [
                {"index": 0, "codec_type": "video", "width": 1920, "height": 1080},
                {"index": 1, "codec_type": "audio", "channels": 2},
                {"index": 2, "codec_type": "subtitle", "codec_name": "subrip"},
            ],
            "format": {},
        },
    )
    util.save_probe_result(
        2,
        {
            "streams": [
                {"index": 0, "codec_type": "audio", "channels": 2},
            ],
            "format": {},
        },
    )

    stats = util.get_stats()

    assert stats.probed_files == 2
    assert stats.video_streams == 1
    assert stats.audio_streams == 2
    assert stats.subtitle_streams == 1
    assert stats.last_probed is not None
