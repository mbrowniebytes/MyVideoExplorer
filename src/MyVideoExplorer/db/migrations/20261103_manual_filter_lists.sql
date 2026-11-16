ALTER TABLE media_filters
    ADD COLUMN IF NOT EXISTS sort_option VARCHAR DEFAULT 'default';

ALTER TABLE media_filters
    ADD COLUMN IF NOT EXISTS needs_rebuild BOOLEAN DEFAULT FALSE;

UPDATE media_filters SET sort_option = 'default' WHERE sort_option IS NULL;
UPDATE media_filters SET needs_rebuild = FALSE WHERE needs_rebuild IS NULL;

ALTER TABLE media_filters ALTER COLUMN sort_option SET NOT NULL;
ALTER TABLE media_filters ALTER COLUMN needs_rebuild SET NOT NULL;

CREATE TABLE IF NOT EXISTS filter_manual_list (
    filter_id BIGINT NOT NULL,
    order_index INTEGER NOT NULL,
    media_folder VARCHAR NOT NULL,
    media_id BIGINT NOT NULL,
    rel_path VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'exists'
        CHECK (status IN ('exists', 'missing')),
    PRIMARY KEY (filter_id, media_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fml_order
    ON filter_manual_list (filter_id, order_index);
