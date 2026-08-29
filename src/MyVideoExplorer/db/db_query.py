class DbQuery:
    class MediaFile:
        UPSERT_MEDIA = """
            INSERT INTO media_file (media_path, file_path, type, title, year, plot, score, rated, runtime, tags, genres, actors, directors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (file_path) DO UPDATE SET
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
                modified_at = now()
        """

        SELECT_ALL_PATHS = "SELECT file_path FROM media_file"

        SELECT_METADATA = "SELECT title, year, plot, score, rated, runtime, tags, genres, actors, directors FROM media_file WHERE file_path = ?"

        DELETE_BY_DIR_NOT_IN = "DELETE FROM media_file WHERE media_path LIKE ? AND file_path NOT IN (SELECT unnest(?::VARCHAR[]))"

        DELETE_ALL_BY_DIR = "DELETE FROM media_file WHERE media_path LIKE ?"

    class MediaPathStats:
        INSERT = """
            INSERT OR REPLACE INTO media_path_stats (
                media_path, subfolders_count, files_count, images_count,
                videos_count, nfo_count, other_count, last_scanned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        SELECT = "SELECT * FROM media_path_stats WHERE media_path = ?"

        DELETE = "DELETE FROM media_path_stats WHERE media_path = ?"

