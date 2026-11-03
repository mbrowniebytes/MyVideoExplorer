from __future__ import annotations

import datetime
import shutil
from pathlib import Path


def backup_database(db_path: str) -> None:
    """Create a daily backup of a DuckDB database before mutations.

    Backups are stored in a ``backups/`` subdirectory next to the database,
    named ``{stem}_{YYYY-MM-DD}.db``.  Only one backup per day is kept, and
    at most 5 of the most recent backups are retained.
    """
    if not Path(db_path).exists():
        return

    db_path_obj = Path(db_path)
    backup_dir = db_path_obj.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    today_str = datetime.datetime.now(datetime.UTC).astimezone().strftime("%Y-%m-%d")
    backup_name = f"{db_path_obj.stem}_{today_str}{db_path_obj.suffix}"
    backup_path = backup_dir / backup_name

    # Only create one backup per day
    if not backup_path.exists():
        try:
            shutil.copy2(db_path, backup_path)
        except OSError:
            return

    # Keep 5 most recent backups
    backup_pattern = f"{db_path_obj.stem}_*{db_path_obj.suffix}"
    backups = sorted(
        backup_dir.glob(backup_pattern),
        reverse=True,
        key=lambda p: p.stat().st_mtime,
    )

    max_backups = 5
    for old_backup in backups[max_backups:]:
        try:
            old_backup.unlink()
        except OSError:
            pass
