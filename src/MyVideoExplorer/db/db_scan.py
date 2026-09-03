import duckdb
from typing import Any
from MyVideoExplorer.db import db_query, db_migrations

class DbScanUtil:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        db_migrations.DbMigrations(self.db_path).run_migrations()

    def save_stats(self, stats: dict[str, Any], progress_callback=None):
        if progress_callback is not None:
            progress_callback(0, "Saving stats")
        con = duckdb.connect(self.db_path)
        con.execute(db_query.DbQuery.MediaPathStats.INSERT, (
            stats['media_path'], stats['subfolders_count'], stats['files_count'],
            stats['images_count'], stats['videos_count'], stats['nfo_count'],
            stats['other_count'], stats['last_scanned']
        ))
        con.close()
        if progress_callback is not None:
            progress_callback(100, "Saved stats")

    def get_stats(self, media_path: str):
        con = duckdb.connect(self.db_path)
        res = con.execute(db_query.DbQuery.MediaPathStats.SELECT, (media_path,)).fetchone()
        con.close()
        return res

    def delete_stats(self, media_path: str):
        con = duckdb.connect(self.db_path)
        con.execute(db_query.DbQuery.MediaPathStats.DELETE, (media_path,))
        con.close()

    def save_media(self, media_list: list[dict[str, Any]], media_path: str, progress_callback=None):
        con = duckdb.connect(self.db_path)

        if progress_callback is not None:
            progress_callback(10, "Cleaning old media rows")

        # 1. Delete records for the scanned folder that are no longer present
        if media_list:
            # Prepare a list of paths
            incoming_paths = [item.get('file_path') for item in media_list]
            # Use tuple for IN clause
            con.execute(db_query.DbQuery.MediaFile.DELETE_BY_DIR_NOT_IN, (f"{media_path}%", incoming_paths))
        else:
            # If no media found, all files in this folder are gone
            # con.execute(db_query.DbQuery.MediaFile.DELETE_ALL_BY_DIR, (f"{media_path}%",))
            self.delete_stats(media_path)

        if not media_list:
            con.close()
            if progress_callback is not None:
                progress_callback(100, "Saved media rows")
            return

        if progress_callback is not None:
            progress_callback(25, "Preparing media rows")

        # Prepare data for insertion
        data = []
        for idx, item in enumerate(media_list):
            metadata = item.get('metadata') or {}

            # Validation & Conversion
            year = metadata.get('year')
            if year == '' or year is None:
                year = None
            else:
                try:
                    year = int(year)
                except (ValueError, TypeError):
                    year = None

            runtime = metadata.get('runtime')
            if runtime == '' or runtime is None:
                runtime = 0
            else:
                try:
                    runtime = int(runtime) * 60  # Convert minutes to seconds
                except (ValueError, TypeError):
                    runtime = 0

            data.append((
                media_path,
                item.get('file_path'),
                item.get('type') or 'video',
                metadata.get('title'),
                year,
                metadata.get('plot'),
                metadata.get('score'),
                metadata.get('rated'),
                runtime,
                metadata.get('tags'),
                metadata.get('genres'),
                metadata.get('actors'),
                metadata.get('directors'),
            ))

            if progress_callback is not None and len(media_list) > 1:
                pct = int((idx + 1) / len(media_list) * 60) + 25
                progress_callback(pct, "Saving media rows")

        # Use UPSERT to update or add media
        con.executemany(db_query.DbQuery.MediaFile.UPSERT_MEDIA, data)
        con.close()
        if progress_callback is not None:
            progress_callback(100, "Saved media rows")
