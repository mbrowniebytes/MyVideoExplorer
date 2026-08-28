import duckdb
import json
import os
from typing import Any
from MyVideoExplorer.db import db_query

class DbScanUtil:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        con = duckdb.connect(self.db_path)
        for stmt in db_query.DbQuery.get_all_create_statements():
            con.execute(stmt)
        con.close()

    def save_stats(self, stats: dict[str, Any]):
        con = duckdb.connect(self.db_path)
        con.execute(db_query.DbQuery.FolderStats.INSERT, (
            stats['folder_path'], stats['subfolders_count'], stats['files_count'],
            stats['images_count'], stats['videos_count'], stats['nfo_count'],
            stats['other_count'], stats['last_scanned']
        ))
        con.close()

    def get_stats(self, folder_path: str):
        con = duckdb.connect(self.db_path)
        res = con.execute(db_query.DbQuery.FolderStats.SELECT, (folder_path,)).fetchone()
        con.close()
        return res

    def save_media(self, media_list: list[dict[str, Any]], folder_path: str):
        con = duckdb.connect(self.db_path)

        # 1. Delete records for the scanned folder that are no longer present
        if media_list:
            # Prepare a list of paths
            incoming_paths = [item.get('path') for item in media_list]
            # Use tuple for IN clause
            con.execute(db_query.DbQuery.MediaFile.DELETE_BY_DIR_NOT_IN, (f"{folder_path}%", incoming_paths))
        else:
            # If no media found, all files in this folder are gone
            con.execute(db_query.DbQuery.MediaFile.DELETE_ALL_BY_DIR, (f"{folder_path}%",))

        if not media_list:
            con.close()
            return

        # Prepare data for insertion
        data = []
        for item in media_list:
            metadata = item.get('metadata') or {}
            data.append((
                item.get('path'),
                item.get('dir') or os.path.dirname(item.get('path', '')),
                item.get('type') or 'video',
                metadata.get('title'),
                metadata.get('year'),
                metadata.get('plot'),
                metadata.get('score'),
                metadata.get('rated'),
                metadata.get('runtime'),
                metadata.get('tags'),
                metadata.get('genres'),
                metadata.get('actors'),
                metadata.get('directors'),
                json.dumps(metadata.get('services'))
            ))

        # Create a temporary table with the incoming data
        con.execute(db_query.DbQuery.MediaFile.CREATE_TEMP_INCOMING, data[0])
        con.executemany(db_query.DbQuery.MediaFile.INSERT_INTO_INCOMING, data)

        # Use MERGE to upsert
        con.execute(db_query.DbQuery.MediaFile.MERGE)
        con.close()
