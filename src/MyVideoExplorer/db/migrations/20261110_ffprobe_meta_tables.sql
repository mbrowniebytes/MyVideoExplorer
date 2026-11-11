-- media_file_video (per video stream; usually 1 row per file)
CREATE TABLE IF NOT EXISTS media_file_video (
    id BIGINT PRIMARY KEY,
    media_file_id BIGINT NOT NULL REFERENCES media_file(id),
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

-- media_file_audio (per audio stream)
CREATE TABLE IF NOT EXISTS media_file_audio (
    id BIGINT PRIMARY KEY,
    media_file_id BIGINT NOT NULL REFERENCES media_file(id),
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

-- media_file_subtitle (per subtitle stream)
CREATE TABLE IF NOT EXISTS media_file_subtitle (
    id BIGINT PRIMARY KEY,
    media_file_id BIGINT NOT NULL REFERENCES media_file(id),
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
