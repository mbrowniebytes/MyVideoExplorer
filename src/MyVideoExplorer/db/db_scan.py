import duckdb
import json
import os
from typing import Any

class DbScanUtil:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        con = duckdb.connect(self.db_path)
        con.execute("CREATE SEQUENCE IF NOT EXISTS media_id_seq")
        con.execute("""
            CREATE TABLE IF NOT EXISTS media_file (
                id INTEGER PRIMARY KEY DEFAULT nextval('media_id_seq'),
                path TEXT,
                dir TEXT,
                type TEXT,
                title TEXT,
                year INTEGER,
                plot TEXT,
                score DECIMAL(4,2),
                rated TEXT,
                runtime INTEGER,
                tags VARCHAR[],
                genres VARCHAR[],
                actors VARCHAR[],
                directors VARCHAR[],
                services JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_media_path ON media_file(path)")
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

    def save_media(self, media_list: list[dict[str, Any]], folder_path: str):
        con = duckdb.connect(self.db_path)
        
        # 1. Delete records for the scanned folder that are no longer present
        if media_list:
            # Prepare a list of paths
            incoming_paths = [item.get('path') for item in media_list]
            # Use tuple for IN clause
            con.execute("DELETE FROM media_file WHERE dir LIKE ? AND path NOT IN (SELECT unnest(?::VARCHAR[]))", (f"{folder_path}%", incoming_paths))
        else:
            # If no media found, all files in this folder are gone
            con.execute("DELETE FROM media_file WHERE dir LIKE ?", (f"{folder_path}%",))
        
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
        con.execute("CREATE OR REPLACE TEMP TABLE incoming_media AS SELECT * FROM (SELECT ? AS path, ? AS dir, ? AS type, ? AS title, ? AS year, ? AS plot, ? AS score, ? AS rated, ? AS runtime, ? AS tags, ? AS genres, ? AS actors, ? AS directors, ? AS services) WHERE 1=0", data[0])
        con.executemany("INSERT INTO incoming_media VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
        
        # Use MERGE to upsert
        con.execute("""
            MERGE INTO media_file USING incoming_media ON media_file.path = incoming_media.path
            WHEN MATCHED THEN
                UPDATE SET
                    dir = incoming_media.dir,
                    type = incoming_media.type,
                    title = incoming_media.title,
                    year = incoming_media.year,
                    plot = incoming_media.plot,
                    score = incoming_media.score,
                    rated = incoming_media.rated,
                    runtime = incoming_media.runtime,
                    tags = incoming_media.tags,
                    genres = incoming_media.genres,
                    actors = incoming_media.actors,
                    directors = incoming_media.directors,
                    services = incoming_media.services,
                    modified_at = CURRENT_TIMESTAMP
            WHEN NOT MATCHED THEN
                INSERT (path, dir, type, title, year, plot, score, rated, runtime, tags, genres, actors, directors, services)
                VALUES (incoming_media.path, incoming_media.dir, incoming_media.type, incoming_media.title, incoming_media.year, incoming_media.plot, incoming_media.score, incoming_media.rated, incoming_media.runtime, incoming_media.tags, incoming_media.genres, incoming_media.actors, incoming_media.directors, incoming_media.services)
        """)
        con.close()
