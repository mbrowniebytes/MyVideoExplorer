import duckdb
import os
from pathlib import Path

class DbMigrations:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent / "migrations"

    def run_migrations(self):
        con = duckdb.connect(self.db_path)

        # Check if schema_migrations table exists
        table_exists = False
        try:
            res = con.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations'").fetchone()
            if res:
                table_exists = True
        except Exception:
            pass

        applied = []
        if table_exists:
            applied = [row[0] for row in con.execute("SELECT version FROM schema_migrations").fetchall()]

        # Get available migrations
        migration_files = sorted(
            [f for f in os.listdir(self.migrations_dir) if f.endswith(".sql")]
        )

        for migration_file in migration_files:
            if migration_file not in applied:
                print(f"Applying migration: {migration_file}")
                with open(self.migrations_dir / migration_file) as f:
                    sql = f.read()
                    con.execute(sql)

                    con.execute("INSERT INTO schema_migrations (version) VALUES (?)", (migration_file,))
        con.close()
