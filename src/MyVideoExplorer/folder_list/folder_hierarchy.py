from MyVideoExplorer.utils.file_util import FileUtils
from MyVideoExplorer.utils.file_util_model import FileUtilModel


def merge_folder_rows(
    items: list[FileUtilModel],
    folders_by_path: dict[str, FileUtilModel],
    folders: list[FileUtilModel],
) -> None:
    """Deduplicate folders within one media root and prefer media-folder icons."""
    for folder in folders:
        normalized_path = _normalize_path(folder.full_path).casefold()
        existing = folders_by_path.get(normalized_path)
        if existing is None:
            folders_by_path[normalized_path] = folder
            items.append(folder)
        elif folder.icon_name is None:
            existing.icon_name = None


def build_folder_rows(file_path: str, media_root: str) -> list[FileUtilModel]:
    """Return a media file's parent folders, marking derived ancestors as open folders."""
    normalized_file_path = _normalize_path(file_path)
    normalized_root = _normalize_path(media_root)
    if not normalized_file_path or not normalized_root:
        return []

    if not FileUtils.is_same_or_descendant(normalized_file_path, normalized_root):
        return []
    if normalized_file_path.casefold() == normalized_root.casefold():
        return []

    relative_parts = [
        part for part in normalized_file_path[len(normalized_root) :].split("/") if part
    ]
    directory_parts = relative_parts[:-1]
    return [
        FileUtilModel(
            type="dir",
            name=part,
            full_path=FileUtils.join(normalized_root, *directory_parts[:index]),
            depth=index - 1,
            icon_name="fa6s.folder-open" if index < len(directory_parts) else None,
        )
        for index, part in enumerate(directory_parts, start=1)
    ]


def _normalize_path(path: str) -> str:
    return FileUtils.normalize_path(path)
