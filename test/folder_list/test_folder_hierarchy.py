from MyVideoExplorer.folder_list.folder_hierarchy import build_folder_rows


def test_build_folder_rows_marks_ancestors_open_and_excludes_root():
    items = build_folder_rows(
        "C:\\Movies\\TV\\Show\\Season 1\\episode.mkv",
        "C:/Movies",
    )

    assert [
        (item.full_path, item.name, item.depth, item.icon_name) for item in items
    ] == [
        ("C:/Movies/TV", "TV", 0, "fa6s.folder-open"),
        ("C:/Movies/TV/Show", "Show", 1, "fa6s.folder-open"),
        ("C:/Movies/TV/Show/Season 1", "Season 1", 2, None),
    ]


def test_build_folder_rows_rejects_paths_outside_root():
    assert build_folder_rows("/media/movies-extra/Film/film.mkv", "/media/movies") == []


def test_build_folder_rows_omits_root_for_root_level_files():
    assert build_folder_rows("/media/movies/film.mkv", "/media/movies") == []
