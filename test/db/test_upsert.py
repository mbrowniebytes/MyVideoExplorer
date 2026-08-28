from MyVideoExplorer.db.db_scan import DbScanUtil
import duckdb

# Re-init db
db_util = DbScanUtil('db/test_upsert.db')

# Initial data
media_list_1 = [
    {
        'path': 'path/to/movie1.mp4',
        'dir': 'path/to',
        'title': 'Test Movie 1',
        'year': 2023,
    }
]
db_util.save_media(media_list_1, 'path/to')

# Update data
media_list_2 = [
    {
        'path': 'path/to/movie1.mp4',
        'dir': 'path/to',
        'title': 'Updated Movie 1',
        'year': 2024,
    },
    {
        'path': 'path/to/movie2.mp4',
        'dir': 'path/to',
        'title': 'New Movie 2',
        'year': 2025,
    }
]
db_util.save_media(media_list_2, 'path/to')

con = duckdb.connect('db/test_upsert.db')
print("Data in media_file:")
for row in con.execute("SELECT path, title, year FROM media_file ORDER BY path").fetchall():
    print(row)
con.close()
