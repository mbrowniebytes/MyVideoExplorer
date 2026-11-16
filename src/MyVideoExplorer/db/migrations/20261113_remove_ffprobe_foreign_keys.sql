-- Recreate ffprobe meta tables without foreign key constraints to allow UPDATEs on media_file.
-- DuckDB blocks UPDATEs on parent rows still referenced by foreign keys, even when
-- the primary key is unchanged.  DuckDB does not support DROP CONSTRAINT for foreign keys,
-- so the tables must be recreated.  These tables are a dumb data store, so application-
-- level referential integrity is sufficient.

-- media_file_video
CREATE TABLE IF NOT EXISTS media_file_video_new (
    id BIGINT PRIMARY KEY,
    media_file_id BIGINT NOT NULL,
    stream_index INTEGER NOT NULL,
    width INTEGER,
    height INTEGER,
    codec_name VARCHAR(32),
    codec_long_name VARCHAR(128),
    profile VARCHAR(64),
    pix_fmt VARCHAR(32),
    framerate VARCHAR(16),
    bitrate BIGINT,
    duration_s DOUBLE,
    color_range VARCHAR(16),
    color_space VARCHAR(32),
    color_transfer VARCHAR(32),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(media_file_id, stream_index)
);
INSERT INTO media_file_video_new SELECT * FROM media_file_video;
DROP TABLE IF EXISTS media_file_video;
ALTER TABLE media_file_video_new RENAME TO media_file_video;

-- media_file_audio
CREATE TABLE IF NOT EXISTS media_file_audio_new (
    id BIGINT PRIMARY KEY,
    media_file_id BIGINT NOT NULL,
    stream_index INTEGER NOT NULL,
    codec_name VARCHAR(32),
    profile VARCHAR(64),
    channels INTEGER,
    channel_layout VARCHAR(32),
    sample_rate INTEGER,
    bitrate BIGINT,
    lang VARCHAR(8),
    default_track BOOLEAN,
    forced BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(media_file_id, stream_index)
);
INSERT INTO media_file_audio_new SELECT * FROM media_file_audio;
DROP TABLE IF EXISTS media_file_audio;
ALTER TABLE media_file_audio_new RENAME TO media_file_audio;

-- media_file_subtitle
CREATE TABLE IF NOT EXISTS media_file_subtitle_new (
    id BIGINT PRIMARY KEY,
    media_file_id BIGINT NOT NULL,
    stream_index INTEGER NOT NULL,
    format VARCHAR(32),
    lang VARCHAR(8),
    is_default BOOLEAN,
    is_forced BOOLEAN,
    title VARCHAR(256),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(media_file_id, stream_index)
);
INSERT INTO media_file_subtitle_new SELECT * FROM media_file_subtitle;
DROP TABLE IF EXISTS media_file_subtitle;
ALTER TABLE media_file_subtitle_new RENAME TO media_file_subtitle;
