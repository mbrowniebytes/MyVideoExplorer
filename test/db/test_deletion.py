import os
from MyVideoExplorer.db.db_scan import DbScanUtil
import duckdb

# Re-init db
os.makedirs("tmp/db", exist_ok=True)
db_util = DbScanUtil('tmp/db/test_deletion.db')

# Initial data: 2 files
media_list_1 = [
    {
        'path': 'path/to/movie1.mp4',
        'dir': 'path/to',
        'title': 'Movie 1',
    },
    {
        'path': 'path/to/movie2.mp4',
        'dir': 'path/to',
        'title': 'Movie 2',
    }
]
db_util.save_media(media_list_1, 'path/to')

# Update data: 1 file (movie2.mp4 deleted)
media_list_2 = [
    {
        'path': 'path/to/movie1.mp4',
        'dir': 'path/to',
        'title': 'Movie 1',
    }
]
db_util.save_media(media_list_2, 'path/to')

con = duckdb.connect('tmp/db/test_deletion.db')
print("Data in media_file (should only have Movie 1):")
for row in con.execute("SELECT file_path, title FROM media_file").fetchall():
    print(row)
con.close()
