import duckdb
import json
from typing import Any

class DbScanUtil:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        con = duckdb.connect(self.db_path)
        con.execute("CREATE SEQUENCE IF NOT EXISTS media_id_seq")
        con.execute("""
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY DEFAULT nextval('media_id_seq'),
                path VARCHAR(255),
                metadata JSON
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS folder_stats (
                folder_path VARCHAR(255) PRIMARY KEY,
                subfolders_count INTEGER,
                files_count INTEGER,
                images_count INTEGER,
                videos_count INTEGER,
                nfo_count INTEGER,
                other_count INTEGER,
                last_scanned TIMESTAMP
            )
        """)
        con.close()

    def save_stats(self, stats: dict[str, Any]):
        con = duckdb.connect(self.db_path)
        con.execute("""
            INSERT OR REPLACE INTO folder_stats (
                folder_path, subfolders_count, files_count, images_count,
                videos_count, nfo_count, other_count, last_scanned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stats['folder_path'], stats['subfolders_count'], stats['files_count'],
            stats['images_count'], stats['videos_count'], stats['nfo_count'],
            stats['other_count'], stats['last_scanned']
        ))
        con.close()

    def get_stats(self, folder_path: str):
        con = duckdb.connect(self.db_path)
        res = con.execute("SELECT * FROM folder_stats WHERE folder_path = ?", (folder_path,)).fetchone()
        con.close()
        return res

    def save_media(self, media_list: list[dict[str, Any]]):
        con = duckdb.connect(self.db_path)
        # Clear existing media for simplicity if we are overwriting
        con.execute("DELETE FROM media")

        # Prepare data for insertion
        # Using a list of tuples for executemany
        data = []
        for item in media_list:
            path = item.get('path', '')
            metadata = item.get('metadata')
            data.append((path, json.dumps(metadata) if metadata else None))

        if data:
            con.executemany("INSERT INTO media (id, path, metadata) VALUES (nextval('media_id_seq'), ?, ?)", data)

        con.close()
