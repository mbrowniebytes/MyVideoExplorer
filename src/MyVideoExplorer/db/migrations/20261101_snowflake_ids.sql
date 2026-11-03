-- Migrate media_file.id from INTEGER (SEQUENCE) to BIGINT (snowflake IDs)
-- DuckDB cannot ALTER a PRIMARY KEY column type, so we recreate the table.
-- The Python migration code (_reassign_to_snowflake_ids) runs first and
-- populates _id_mapping with snowflake IDs for each old ID.

DROP SEQUENCE IF EXISTS media_id_seq;

CREATE TABLE IF NOT EXISTS media_file_new (
    id BIGINT PRIMARY KEY,
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
    qty_played INTEGER DEFAULT 0,
    last_played DATE,
    user_tags VARCHAR[] DEFAULT [],
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO media_file_new
    (id, media_path, file_path, type, title, year, plot, score, rated, runtime,
     tags, genres, actors, directors, qty_played, last_played, user_tags,
     created_at, modified_at)
SELECT
    COALESCE(m.new_id, mf.id::BIGINT), mf.media_path, mf.file_path, mf.type, mf.title, mf.year, mf.plot, mf.score, mf.rated, mf.runtime,
    mf.tags, mf.genres, mf.actors, mf.directors, mf.qty_played, mf.last_played, mf.user_tags,
    mf.created_at, mf.modified_at
FROM media_file mf
LEFT JOIN _id_mapping m ON mf.id = m.old_id;

DROP TABLE media_file;
ALTER TABLE media_file_new RENAME TO media_file;

DROP TABLE IF EXISTS _id_mapping;

CREATE UNIQUE INDEX IF NOT EXISTS idx_file_path ON media_file(file_path);
