# Database Migrations

This directory contains incremental SQL migration files for the three DuckDB databases used by MyVideoExplorer.

## Migration Pattern

The project uses **multiple incremental migration files** rather than a single cumulative schema file. Each migration is a self-contained patch that documents a single schema change. This is the industry standard pattern used by tools like Flyway, Liquibase, and Alembic.

**Why incremental migrations:**
- Each file documents one change — easy to understand in isolation
- New databases start clean: only unapplied migrations run
- The filename serves as the version tracker
- Changes are naturally ordered by date-stamped filenames
- If a migration fails, you know exactly which change caused it
- The `schema_migrations` table tracks which migrations have been applied

## Database Types

The project maintains **three separate databases**, each with its own set of migrations:

| Database | Description | Header Value |
|----------|-------------|--------------|
| `media.db` | Main media catalog (files, metadata, play history) | `"media"` |
| `filter_catalog.db` | User-defined filters and filter groups | `"filter_catalog"` |
| `tag_catalog.db` | Tag catalog for browsing and filtering | `"tag_catalog"` |

## File Naming Convention

All migration files follow the pattern:

```
YYYYMMDD_description.sql
```

- **Date prefix**: Use the date the migration was created (e.g., `20261115`)
- **Description**: Brief snake_case description of the change (e.g., `add_file_size`)
- **Example**: `20261115_add_file_size.sql`

Files are executed in alphabetical order, so the date prefix ensures correct ordering.

## Required Header Format

**Every migration file MUST start with a Liquibase-style multiline header comment block:**

```sql
-- @migration
-- db: media
-- purpose: Brief description of what this migration does
```

### Header Fields

| Field | Required | Description |
|-------|----------|-------------|
| `db` | **Yes** | Target database: `media`, `filter_catalog`, or `tag_catalog` |
| `purpose` | **Yes** | One-line description of what the migration does |
| `python_pre_step` | No | Python method name to run before SQL (see below) |

### Examples

**Simple migration (no Python pre-step):**
```sql
-- @migration
-- db: media
-- purpose: Add file_size column to media_file table
ALTER TABLE media_file ADD COLUMN IF NOT EXISTS file_size BIGINT;
```

**Migration with Python pre-step:**
```sql
-- @migration
-- db: media
-- purpose: Recreate media_file with BIGINT PK using snowflake IDs
-- python_pre_step: reassign_snowflake_ids
-- SQL that uses the _id_mapping table built by the Python pre-step
```

## How to Create a New Migration

1. **Create a new file** in this directory with the naming convention `YYYYMMDD_description.sql`
2. **Add the header comment block** at the top with `db` and `purpose` fields
3. **Write the SQL** — use `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE`, etc.
4. **If the migration needs Python pre-steps** (data transformation before SQL), add the `python_pre_step` field and implement the method in `db_migrations.py`
5. **Do NOT edit existing migration files** — always create a new file for new changes

## Python Pre-Steps

Some migrations require Python code to run **before** the SQL executes (e.g., data transformation, ID reassignment).

### How to Add a Python Pre-Step

1. In the migration SQL file, add `-- python_pre_step: method_name` to the header block
2. In `db_migrations.py`, add the method name to the `_pre_step_dispatch` dict in `run_migrations()`
3. Implement the method in the `DbMigrations` class

### Current Python Pre-Steps

| Migration File | Python Method | Purpose |
|----------------|---------------|---------|
| `20261027_normalize_posix_paths.sql` | `_normalize_legacy_paths()` | Normalizes path separators and deduplicates rows |
| `20261101_snowflake_ids.sql` | `_reassign_to_snowflake_ids()` | Builds ID mapping table for snowflake ID migration |
| `20261102_filter_snowflake_ids.sql` | `_reassign_filter_to_snowflake_ids()` | Builds filter ID mapping table for snowflake ID migration |

## How Migrations Run

`DbMigrations.run_migrations()` in `db_migrations.py`:

1. Opens the DuckDB connection
2. Checks `schema_migrations` table for already-applied versions
3. Scans this directory for `.sql` files
4. Filters files by parsing the `-- @migration` header comment to match the current database type
5. For each unapplied migration, runs optional Python pre-steps, then executes the SQL
6. Records the migration filename in `schema_migrations`

## Current Migration Files

### media.db (12 files)

| File | Purpose |
|------|---------|
| `20260801_create_media.sql` | Initial schema: media_file, media_path_stats, schema_migrations tables |
| `20260803_add_play_history.sql` | Add qty_played and last_played columns |
| `20260930_add_user_tags.sql` | Add user_tags column |
| `20261027_normalize_posix_paths.sql` | Normalize path separators (Python pre-step only) |
| `20261101_snowflake_ids.sql` | Recreate media_file with BIGINT PK (Python pre-step) |
| `20261110_add_file_size.sql` | Add file_size column |
| `20261110_ffprobe_meta_tables.sql` | Create media_file_video, media_file_audio, media_file_subtitle tables |
| `20261113_remove_ffprobe_foreign_keys.sql` | Recreate ffprobe tables without FK constraints |

### filter_catalog.db (5 files)

| File | Purpose |
|------|---------|
| `20261101_create_filter_catalog.sql` | Initial schema: media_filters table |
| `20261102_filter_snowflake_ids.sql` | Recreate media_filters with BIGINT PK (Python pre-step) |
| `20261103_manual_filter_lists.sql` | Add columns, create filter_manual_list table |
| `20261104_filter_groups.sql` | Create filter_groups table, add group columns |

### tag_catalog.db (1 file)

| File | Purpose |
|------|---------|
| `20261101_create_tag_catalog.sql` | Initial schema: tag_catalog table |

## Instructions for Future AI Agents

**When adding a schema change:**
1. Create a NEW migration file — **do NOT edit existing migrations**
2. Follow the naming convention and header format documented above
3. If the change needs data transformation, implement a Python pre-step
4. Test the migration on a fresh database to ensure it applies cleanly

**When modifying the migration runner:**
- The `-- @migration` header block is the source of truth for routing
- Do not use hardcoded filename prefixes or path-based heuristics
- The header parser reads consecutive `--` comment lines after the `-- @migration` marker
