class DbQuery:
    class MediaFile:
        CREATE_SEQ = "CREATE SEQUENCE IF NOT EXISTS media_id_seq"
        CREATE_TABLE = """
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
        """
        CREATE_INDEX = "CREATE UNIQUE INDEX IF NOT EXISTS idx_media_path ON media_file(path)"
        CREATE_TEMP_INCOMING = "CREATE OR REPLACE TEMP TABLE incoming_media AS SELECT * FROM (SELECT ? AS path, ? AS dir, ? AS type, ? AS title, ? AS year, ? AS plot, ? AS score, ? AS rated, ? AS runtime, ? AS tags, ? AS genres, ? AS actors, ? AS directors, ? AS services) WHERE 1=0"
        INSERT_INTO_INCOMING = "INSERT INTO incoming_media VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        MERGE = """
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
        """
        SELECT_ALL_PATHS = "SELECT path FROM media_file"
        SELECT_METADATA = "SELECT title, year, plot, score, rated, runtime, tags, genres, actors, directors FROM media_file WHERE path = ?"
        DELETE_BY_DIR_NOT_IN = "DELETE FROM media_file WHERE dir LIKE ? AND path NOT IN (SELECT unnest(?::VARCHAR[]))"
        DELETE_ALL_BY_DIR = "DELETE FROM media_file WHERE dir LIKE ?"

    class FolderStats:
        CREATE_TABLE = """
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
        """
        INSERT = """
            INSERT OR REPLACE INTO folder_stats (
                folder_path, subfolders_count, files_count, images_count,
                videos_count, nfo_count, other_count, last_scanned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        SELECT = "SELECT * FROM folder_stats WHERE folder_path = ?"

    @classmethod
    def get_all_create_statements(cls):
        return [
            cls.MediaFile.CREATE_SEQ,
            cls.MediaFile.CREATE_TABLE,
            cls.MediaFile.CREATE_INDEX,
            cls.FolderStats.CREATE_TABLE,
        ]
