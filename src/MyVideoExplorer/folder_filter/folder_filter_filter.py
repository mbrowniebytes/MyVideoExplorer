from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget

from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil


class FolderFilterFilter:
    def __init__(
        self,
        nfo_parse_util: NfoParseUtil,
        folder_configs: list[dict] = None,
        log_util: LogUtil = None,
    ):
        self.log_util = log_util
        self.nfo_parse_util = nfo_parse_util
        self.folder_configs = folder_configs or []
        if self.log_util:
            self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def apply_filters(
        self,
        items: list[FileUtilModel],
        filters: list[dict],
    ) -> list[FileUtilModel]:
        if not filters:
            return self._default_folders(items)

        filtered_items: list[FileUtilModel] = []
        seen_paths: set[str] = set()

        current_dir: FileUtilModel | None = None

        for item in items:
            if item.is_dir:
                current_dir = item

            if current_dir is None:
                continue

            if self._item_matches(item=item, filters=filters):
                if current_dir.full_path and current_dir.full_path not in seen_paths:
                    filtered_items.append(current_dir)
                    seen_paths.add(current_dir.full_path)

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

                if not item.is_file:
                    continue

                if self._matches_file_filter(filter_type, file_name, filter_value):
                    type_match = True
                    break

                if file_type != "nfo":
                    continue

                if filter_type not in {
                    "genre",
                    "actor",
                    "director",
                    "title",
                    "plot",
                }:
                    continue

                movie_info = self.nfo_parse_util.parse_nfo(nfo_file=item.full_path)
                if movie_info is None:
                    continue

                if self._matches_nfo_filter(filter_type, filter_value, movie_info):
                    type_match = True
                    break

            if not type_match:
                return False

        return True

    @staticmethod
    def _matches_folder_filter(
        filter_type: str, file_name: str, filter_value: str
    ) -> bool:
        return (
            filter_type.casefold() == "folder" and filter_value.casefold() in file_name
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
        return filter_type == "file" and filter_value.casefold() in file_name

    def _matches_nfo_filter(
        self,
        filter_type: str,
        filter_value: str,
        movie_info: dict,
    ) -> bool:
        clean_type = filter_type.casefold().strip()
        if clean_type == "genre":
            return self._matches_genre(movie_info, filter_value)

        if clean_type == "actor":
            return self._contains_any(movie_info.get("actors", []), filter_value)

        if clean_type == "director":
            return self._contains_text(movie_info.get("director", ""), filter_value)

        if clean_type == "title":
            return self._contains_text(movie_info.get("title", ""), filter_value)

        if clean_type == "plot":
            return self._contains_text(movie_info.get("plot", ""), filter_value)

        return False

    @staticmethod
    def _matches_genre(movie_info: dict, genre: str) -> bool:
        if not genre:
            return False
        return FolderFilterFilter._contains_any(movie_info.get("genres", []), genre)

    @staticmethod
    def _contains_any(values: list[str], needle: str) -> bool:
        for value in values:
            if needle in value.casefold():
                return True
        return False

    @staticmethod
    def _contains_text(value: str, needle: str) -> bool:
        return bool(value) and needle in value.casefold()

    def apply_theme(self) -> None:
        return
        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.setStyleSheet(APP_THEME.container_qss())

        for child in self.findChildren(QWidget):
            child.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
