class DbQuery:
    class MediaFile:
        UPSERT_MEDIA = """
            INSERT INTO media_file (id, media_path, file_path, type, title, year, plot, score, rated, runtime, tags, genres, actors, directors, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (file_path) DO UPDATE SET
                id = EXCLUDED.id,
                file_path = EXCLUDED.file_path,
                type = EXCLUDED.type,
                title = EXCLUDED.title,
                year = EXCLUDED.year,
                plot = EXCLUDED.plot,
                score = EXCLUDED.score,
                rated = EXCLUDED.rated,
                runtime = EXCLUDED.runtime,
                tags = EXCLUDED.tags,
                genres = EXCLUDED.genres,
                actors = EXCLUDED.actors,
                directors = EXCLUDED.directors,
                file_size = EXCLUDED.file_size,
                modified_at = NOW()
        """

        SELECT_ALL_PATHS = "SELECT file_path FROM media_file"

        SELECT_METADATA = "SELECT title, year, plot, score, rated, runtime, tags, genres, actors, directors FROM media_file WHERE file_path = ?"

        DELETE_BY_DIR_NOT_IN = "DELETE FROM media_file WHERE media_path = ? AND file_path NOT IN (SELECT unnest(?::VARCHAR[]))"

        DELETE_ALL_BY_DIR = "DELETE FROM media_file WHERE media_path = ?"

        SELECT_VIDEO_FILES = """
            SELECT id, file_path FROM media_file
            WHERE LOWER(SUBSTR(file_path, LENGTH(file_path) - POSITION('.' IN REVERSE(file_path)) + 1))
            IN (SELECT unnest(?::VARCHAR[]))
        """

    class FfprobeVideo:
        UPSERT = """
            INSERT INTO media_file_video (
                id, media_file_id, stream_index, width, height, codec_name, codec_long_name,
                profile, pix_fmt, framerate, bitrate, duration_s, color_range, color_space, color_transfer
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (media_file_id, stream_index) DO UPDATE SET
                width = EXCLUDED.width,
                height = EXCLUDED.height,
                codec_name = EXCLUDED.codec_name,
                codec_long_name = EXCLUDED.codec_long_name,
                profile = EXCLUDED.profile,
                pix_fmt = EXCLUDED.pix_fmt,
                framerate = EXCLUDED.framerate,
                bitrate = EXCLUDED.bitrate,
                duration_s = EXCLUDED.duration_s,
                color_range = EXCLUDED.color_range,
                color_space = EXCLUDED.color_space,
                color_transfer = EXCLUDED.color_transfer,
                modified_at = NOW()
        """

        SELECT_SCANNED_IDS = "SELECT DISTINCT media_file_id FROM media_file_video"

        DELETE_BY_FILE = "DELETE FROM media_file_video WHERE media_file_id = ?"

        DELETE_BY_DIR = """
            DELETE FROM media_file_video
            WHERE media_file_id IN (
                SELECT id FROM media_file WHERE media_path = ?
            )
        """

    class FfprobeAudio:
        UPSERT = """
            INSERT INTO media_file_audio (
                id, media_file_id, stream_index, codec_name, profile, channels,
                channel_layout, sample_rate, bitrate, lang, default_track, forced
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (media_file_id, stream_index) DO UPDATE SET
                codec_name = EXCLUDED.codec_name,
                profile = EXCLUDED.profile,
                channels = EXCLUDED.channels,
                channel_layout = EXCLUDED.channel_layout,
                sample_rate = EXCLUDED.sample_rate,
                bitrate = EXCLUDED.bitrate,
                lang = EXCLUDED.lang,
                default_track = EXCLUDED.default_track,
                forced = EXCLUDED.forced,
                modified_at = NOW()
        """

        DELETE_BY_FILE = "DELETE FROM media_file_audio WHERE media_file_id = ?"

        DELETE_BY_DIR = """
            DELETE FROM media_file_audio
            WHERE media_file_id IN (
                SELECT id FROM media_file WHERE media_path = ?
            )
        """

    class FfprobeSubtitle:
        UPSERT = """
            INSERT INTO media_file_subtitle (
                id, media_file_id, stream_index, format, lang, is_default, is_forced, title
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (media_file_id, stream_index) DO UPDATE SET
                format = EXCLUDED.format,
                lang = EXCLUDED.lang,
                is_default = EXCLUDED.is_default,
                is_forced = EXCLUDED.is_forced,
                title = EXCLUDED.title,
                modified_at = NOW()
        """

        DELETE_BY_FILE = "DELETE FROM media_file_subtitle WHERE media_file_id = ?"

        DELETE_BY_DIR = """
            DELETE FROM media_file_subtitle
            WHERE media_file_id IN (
                SELECT id FROM media_file WHERE media_path = ?
            )
        """

    class FfprobeStats:
        SELECT = """
            SELECT
                (SELECT COUNT(*) FROM (
                    SELECT media_file_id FROM media_file_video
                    UNION
                    SELECT media_file_id FROM media_file_audio
                    UNION
                    SELECT media_file_id FROM media_file_subtitle
                )),
                (SELECT COUNT(*) FROM media_file_video),
                (SELECT COUNT(*) FROM media_file_audio),
                (SELECT COUNT(*) FROM media_file_subtitle),
                (SELECT MAX(modified_at) FROM (
                    SELECT modified_at FROM media_file_video
                    UNION ALL
                    SELECT modified_at FROM media_file_audio
                    UNION ALL
                    SELECT modified_at FROM media_file_subtitle
                ))
        """

    class MediaPathStats:
        INSERT = """
            INSERT OR REPLACE INTO media_path_stats (
                media_path, subfolders_count, files_count, images_count,
                videos_count, nfo_count, other_count, last_scanned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        SELECT = """
            SELECT media_path, subfolders_count, files_count, images_count,
                videos_count, nfo_count, other_count, last_scanned
            FROM media_path_stats
            WHERE media_path = ?
        """

        DELETE = "DELETE FROM media_path_stats WHERE media_path = ?"
