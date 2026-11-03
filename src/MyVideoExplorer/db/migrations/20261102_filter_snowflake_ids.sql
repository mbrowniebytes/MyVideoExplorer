-- Migrate media_filters.filter_id from UUID to BIGINT snowflake IDs
-- DuckDB cannot ALTER a PRIMARY KEY column type, so we recreate the table.
-- The Python migration code (_reassign_filter_to_snowflake_ids) runs first
-- and populates _filter_id_mapping with snowflake IDs.

CREATE TABLE IF NOT EXISTS media_filters_new (
    filter_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    criteria JSON NOT NULL,
    folder_counts MAP(VARCHAR, BIGINT) NOT NULL,
    total_count BIGINT,
    sort_order INTEGER NOT NULL
);

INSERT INTO media_filters_new
    (filter_id, name, criteria, folder_counts, total_count, sort_order)
SELECT
    COALESCE(m.new_id, 0), mf.name, mf.criteria, mf.folder_counts, mf.total_count, mf.sort_order
FROM media_filters mf
LEFT JOIN _filter_id_mapping m ON mf.name = m.name;

DROP TABLE media_filters;
ALTER TABLE media_filters_new RENAME TO media_filters;

DROP TABLE IF EXISTS _filter_id_mapping;
