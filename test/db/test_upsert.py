from pathlib import Path

import duckdb

from MyVideoExplorer.db.db_scan import DbScanUtil

# Re-init db
Path("tmp/db").mkdir(parents=True, exist_ok=True)
db_util = DbScanUtil("tmp/db/test_upsert.db")

# Initial data
media_list_1 = [
    {
        "path": "path/to/movie1.mp4",
        "dir": "path/to",
        "title": "Test Movie 1",
        "year": 2023,
    }
]
db_util.save_media(media_list_1, "path/to")

# Update data
media_list_2 = [
    {
        "path": "path/to/movie1.mp4",
        "dir": "path/to",
        "title": "Updated Movie 1",
        "year": 2024,
    },
    {
        "path": "path/to/movie2.mp4",
        "dir": "path/to",
        "title": "New Movie 2",
        "year": 2025,
    },
]
db_util.save_media(media_list_2, "path/to")

con = duckdb.connect("tmp/db/test_upsert.db")
print("Data in media_file:")
for row in con.execute(
    "SELECT file_path, title, year FROM media_file ORDER BY file_path"
).fetchall():
    print(row)
con.close()
