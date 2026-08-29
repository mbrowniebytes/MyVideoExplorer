CREATE SEQUENCE IF NOT EXISTS media_id_seq;
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS media_file (
    id INTEGER PRIMARY KEY DEFAULT nextval('media_id_seq'),
    media_path TEXT,
    file_path TEXT,
    type TEXT,
    title TEXT,
    year SMALLINT,
    plot TEXT,
    score DECIMAL(4,2),
    rated TEXT,
    runtime SMALLINT,
    tags VARCHAR[],
    genres VARCHAR[],
    actors VARCHAR[],
    directors VARCHAR[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_file_path ON media_file(file_path);

CREATE TABLE IF NOT EXISTS media_path_stats (
    media_path TEXT PRIMARY KEY,
    subfolders_count INTEGER,
    files_count INTEGER,
    images_count INTEGER,
    videos_count INTEGER,
    nfo_count INTEGER,
    other_count INTEGER,
    last_scanned TIMESTAMP
);
