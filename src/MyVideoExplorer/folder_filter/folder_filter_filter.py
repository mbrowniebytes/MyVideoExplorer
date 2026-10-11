from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget

from MyVideoExplorer.db import db_query
from MyVideoExplorer.db.models.media_file_metadata import MediaFileMetadata
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil


class FolderFilterFilter:
    def __init__(
        self,
        nfo_parse_util: NfoParseUtil,
        settings_state: SettingsState,
        log_util: LogUtil | None = None,
    ):
        self.log_util = log_util
        self.nfo_parse_util = nfo_parse_util
        self.settings_state = settings_state
        if self.log_util:
            self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def apply_filters(
        self,
        items: list[FileUtilModel],
        filters: list[dict],
    ) -> list[FileUtilModel]:
        if not filters:
            return self._default_folders(items)

        # Separate and group items by directory
        from collections import defaultdict

        dir_items: list[FileUtilModel] = []
        dir_by_path: dict[str, FileUtilModel] = {}
        files_by_dir: dict[str, list[FileUtilModel]] = defaultdict(list)

        for item in items:
            if item.is_dir:
                posix_path = Path(item.full_path).as_posix().casefold()
                if posix_path not in dir_by_path:
                    dir_by_path[posix_path] = item
                    dir_items.append(item)
            elif item.is_file:
                parent_posix = Path(item.full_path).parent.as_posix().casefold()
                files_by_dir[parent_posix].append(item)

        # If there are file items whose parent directories are not explicitly in dir_items,
        # create synthetic folder items for them so they can be matched and returned.
        for parent_posix, files in files_by_dir.items():
            if parent_posix not in dir_by_path and files:
                first_file = files[0]
                parent_path_orig = Path(first_file.full_path).parent.as_posix()
                parent_name = Path(first_file.full_path).parent.name
                dir_item = FileUtilModel(
                    type="dir",
                    name=parent_name,
                    full_path=parent_path_orig,
                    depth=max(0, first_file.depth - 1),
                )
                dir_by_path[parent_posix] = dir_item
                dir_items.append(dir_item)

        # Group filters by type
        grouped_filters = defaultdict(list)
        for f in filters:
            grouped_filters[f["filter"].casefold()].append(f["value"])

        filtered_items: list[FileUtilModel] = []
        seen_paths: set[str] = set()

        for dir_item in dir_items:
            dir_key = Path(dir_item.full_path).as_posix().casefold()
            associated_files = files_by_dir.get(dir_key, [])

            # Check all filter type groups: directory must match all active filter types
            dir_matches = True
            for filter_type, values in grouped_filters.items():
                type_match = False
                for filter_value in values:
                    if filter_type == "media":
                        if self._matches_media_filter(dir_item, filter_value):
                            type_match = True
                            break
                        if any(
                            self._matches_media_filter(f, filter_value)
                            for f in associated_files
                        ):
                            type_match = True
                            break

                    elif filter_type == "folder":
                        if self._matches_folder_filter(
                            filter_type, dir_item.name, filter_value
                        ):
                            type_match = True
                            break

                    elif filter_type == "file":
                        if any(
                            self._matches_file_filter(filter_type, f.name, filter_value)
                            for f in associated_files
                        ):
                            type_match = True
                            break
                        if not associated_files and self._matches_file_filter(
                            filter_type, dir_item.name, filter_value
                        ):
                            type_match = True
                            break

                    elif filter_type in {
                        "genre",
                        "actor",
                        "director",
                        "title",
                        "tag",
                        "nfo",
                    }:
                        for f in associated_files:
                            movie_info = self._get_movie_info(f)
                            if movie_info and self._matches_nfo_filter(
                                filter_type, filter_value, movie_info
                            ):
                                type_match = True
                                break
                        if not associated_files and dir_item.is_dir:
                            movie_info = self._get_movie_info(dir_item)
                            if movie_info and self._matches_nfo_filter(
                                filter_type, filter_value, movie_info
                            ):
                                type_match = True
                                break
                        if type_match:
                            break

                if not type_match:
                    dir_matches = False
                    break

            if dir_matches:
                if dir_item.full_path not in seen_paths:
                    filtered_items.append(dir_item)
                    seen_paths.add(dir_item.full_path)

        return filtered_items

    def _default_folders(self, items: list[FileUtilModel]) -> list[FileUtilModel]:
        filtered_items: list[FileUtilModel] = []
        seen_paths: set[str] = set()

        for item in items:
            if not item.is_dir:
                continue

            if item.full_path in seen_paths:
                continue

            filtered_items.append(item)
            seen_paths.add(item.full_path)

        return filtered_items

    def _item_matches(
        self,
        item: FileUtilModel,
        filters: list[dict],
    ) -> bool:
        file_name = item.name.casefold()
        file_type = item.file_type or ""

        # Group filters by type
        from collections import defaultdict

        grouped_filters = defaultdict(list)
        for f in filters:
            grouped_filters[f["filter"].casefold()].append(f["value"])

        # AND across types, OR within types
        for filter_type, values in grouped_filters.items():
            type_match = False
            for filter_value in values:
                # print(f"filter_type:{filter_type} filter_value:{filter_value}")
                if filter_type == "media":
                    if self._matches_media_filter(item, filter_value):
                        type_match = True
                        break
                    continue

                if item.is_dir:
                    if self._matches_folder_filter(
                        filter_type, file_name, filter_value
                    ):
                        type_match = True
                        break
                    continue

                if item.is_file:
                    if self._matches_file_filter(filter_type, file_name, filter_value):
                        type_match = True
                        break

                    parent_name = Path(item.full_path).parent.name
                    if self._matches_folder_filter(
                        filter_type, parent_name, filter_value
                    ):
                        type_match = True
                        break

                if filter_type not in {
                    "genre",
                    "actor",
                    "director",
                    "title",
                    "tag",
                    "nfo",
                }:
                    continue

                if (
                    not self.settings_state.db_enabled()
                    and file_type != "nfo"
                    and not str(item.full_path).lower().endswith(".nfo")
                ):
                    pass

                movie_info = self._get_movie_info(item)
                if movie_info is None:
                    continue

                if self._matches_nfo_filter(filter_type, filter_value, movie_info):
                    type_match = True
                    break

            if not type_match:
                return False

        return True

    def _get_movie_info(self, item: FileUtilModel) -> dict[str, Any] | None:
        if self.settings_state.db_enabled():
            # Find folder config
            item_path = Path(item.full_path).as_posix()
            for config in self.settings_state.media_configs:
                config_path = Path(config.get("path", "")).as_posix()
                if item_path.casefold().startswith(config_path.casefold()):
                    db_path = self.settings_state.get_db_path(config)
                    if db_path and Path(db_path).exists():
                        # Query DB
                        db_path_str = Path(db_path).as_posix()
                        con = duckdb.connect(db_path_str)
                        try:
                            res = con.execute(
                                """
                                SELECT title, year, plot, score, rated, runtime,
                                       list_concat(coalesce(tags, []), coalesce(user_tags, [])) AS tags,
                                       genres, actors, directors
                                FROM media_file WHERE file_path = ? OR lower(file_path) = lower(?)
                                """,
                                (item_path, item_path),
                            ).fetchone()
                        except Exception:
                            res = con.execute(
                                db_query.DbQuery.MediaFile.SELECT_METADATA,
                                (item.full_path,),
                            ).fetchone()
                        con.close()

                        if res:
                            return MediaFileMetadata(*res).to_movie_info()

        # Fallback to NFO file if present
        if item.file_type == "nfo" or str(item.full_path).lower().endswith(".nfo"):
            return self.nfo_parse_util.parse_nfo(nfo_file=item.full_path)

        if item.is_file:
            nfo_path = Path(item.full_path).with_suffix(".nfo")
            if nfo_path.exists():
                return self.nfo_parse_util.parse_nfo(nfo_file=str(nfo_path))
            movie_nfo = Path(item.full_path).parent / "movie.nfo"
            if movie_nfo.exists():
                return self.nfo_parse_util.parse_nfo(nfo_file=str(movie_nfo))

        if item.is_dir:
            movie_nfo = Path(item.full_path) / "movie.nfo"
            if movie_nfo.exists():
                return self.nfo_parse_util.parse_nfo(nfo_file=str(movie_nfo))

        return None

    @staticmethod
    def _matches_folder_filter(
        filter_type: str, file_name: str, filter_value: str
    ) -> bool:
        return (
            filter_type.casefold() == "folder"
            and filter_value.casefold() in file_name.casefold()
        )

    def _matches_media_filter(
        self, item: FileUtilModel, media_paths: list[str]
    ) -> bool:
        if not media_paths:
            return False

        # Normalize item path
        item_path = item.full_path.replace("\\", "/").casefold()
        item_path_with_slash = item_path if item_path.endswith("/") else item_path + "/"

        for path in media_paths:
            # Normalize and casefold the matching paths, ensuring they end with a slash for clean matching
            normalized_path = path.replace("\\", "/").casefold()
            if not normalized_path.endswith("/"):
                normalized_path += "/"

            # Check if the item's path (normalized) starts with the matching path
            # print(
            #     "fitem_path_with_slash:{item_path_with_slash} normalized_path:{normalized_path}"
            # )
            if item_path_with_slash.startswith(normalized_path):
                return True

        return False

    @staticmethod
    def _matches_file_filter(
        filter_type: str, file_name: str, filter_value: str
    ) -> bool:
        return (
            filter_type.casefold() == "file"
            and filter_value.casefold() in file_name.casefold()
        )

    def _matches_nfo_filter(
        self,
        filter_type: str,
        filter_value: str | list[str],
        movie_info: dict,
    ) -> bool:
        clean_type = filter_type.casefold().strip()
        if clean_type == "genre":
            return self._matches_genre(movie_info, filter_value)

        if clean_type == "tag":
            return self._matches_tag(movie_info, filter_value)

        if clean_type == "actor":
            return self._contains_any(movie_info.get("actors", []), filter_value)

        if clean_type == "director":
            return self._contains_text(movie_info.get("director", ""), filter_value)

        if clean_type == "title":
            return self._contains_text(movie_info.get("title", ""), filter_value)

        if clean_type == "nfo":
            return (
                self._contains_text(movie_info.get("title", ""), filter_value)
                or self._contains_text(movie_info.get("plot", ""), filter_value)
                or self._contains_any(movie_info.get("genres", []), filter_value)
                or self._contains_any(movie_info.get("actors", []), filter_value)
                or self._contains_text(movie_info.get("director", ""), filter_value)
                or self._matches_tag(movie_info, filter_value)
            )

        return False

    @staticmethod
    def _matches_genre(movie_info: dict, genre: str | list[str]) -> bool:
        if not genre:
            return False
        return FolderFilterFilter._contains_any(movie_info.get("genres", []), genre)

    @staticmethod
    def _matches_tag(movie_info: dict, tag: str | list[str]) -> bool:
        if not tag:
            return False
        if isinstance(tag, list):
            return any(FolderFilterFilter._matches_tag(movie_info, t) for t in tag)
        if isinstance(tag, str) and "," in tag:
            tags = [t.strip() for t in tag.split(",") if t.strip()]
            return any(FolderFilterFilter._matches_tag(movie_info, t) for t in tags)
        return FolderFilterFilter._contains_any(
            movie_info.get("tags", []) or [], str(tag)
        )

    @staticmethod
    def _contains_any(values: list[Any], needle: Any) -> bool:
        if isinstance(needle, (list, tuple)):
            return any(FolderFilterFilter._contains_any(values, n) for n in needle)
        needle_fold = str(needle).casefold()
        for value in values:
            if isinstance(value, dict):
                name = str(value.get("name", "") or value.get("tag", "")).casefold()
                if needle_fold in name:
                    return True
            elif isinstance(value, str):
                if needle_fold in value.casefold():
                    return True
        return False

    @staticmethod
    def _contains_text(value: str, needle: str | list[str]) -> bool:
        if isinstance(needle, list):
            return any(FolderFilterFilter._contains_text(value, n) for n in needle)
        return bool(value) and needle.casefold() in str(value).casefold()

    def apply_theme(self) -> None:
        return
        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.setStyleSheet(APP_THEME.container_qss())

        for child in self.findChildren(QWidget):
            child.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
