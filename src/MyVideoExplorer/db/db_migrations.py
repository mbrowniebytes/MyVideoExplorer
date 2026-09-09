from pathlib import Path

import duckdb


class DbMigrations:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent / "migrations"

    def run_migrations(self):
        if not str(self.db_path).strip():
            raise ValueError("Database path is empty. A valid media name is required.")

        db_dir = Path(self.db_path).parent
        if db_dir != Path(""):
            db_dir.mkdir(parents=True, exist_ok=True)

        con = duckdb.connect(self.db_path)
        try:
            # Check if schema_migrations table exists
            table_exists = False
            try:
                res = con.execute(
                    "SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations'"
                ).fetchone()
                if res:
                    table_exists = True
            except Exception:
                pass

            applied = []
            if table_exists:
                applied = [
                    row[0]
                    for row in con.execute(
                        "SELECT version FROM schema_migrations"
                    ).fetchall()
                ]

            # Get available migrations
            migration_files = sorted(
                path.name for path in self.migrations_dir.iterdir() if path.suffix == ".sql"
            )

            for migration_file in migration_files:
                if migration_file not in applied:
                    print(f"Applying migration: {migration_file}")
                    migration_path = self.migrations_dir / migration_file
                    with migration_path.open(encoding="utf-8") as f:
                        sql = f.read()
                        con.execute(sql)

                        con.execute(
                            "INSERT INTO schema_migrations (version) VALUES (?)",
                            (migration_file,),
                        )
        finally:
            con.close()
