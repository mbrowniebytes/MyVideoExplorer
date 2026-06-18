# src/folder_list/folder_list_controller.py
from PySide6.QtCore import QObject
from src.utils.file_util import FileUtil
from src.utils.file_util_model import FileUtilModel
from src.folder_list.folder_list_view import FolderListView
from src.settings.settings import Settings

class FolderListController(QObject):
    def __init__(self, folder_view: FolderListView, file_util: FileUtil, settings: Settings):
        super().__init__()
        self.folder_view = folder_view
        self.file_util = file_util
        self.settings = settings

    def _get_icon_for_path(self, path: str) -> str:
        if not self.settings:
            return "fa5s.folder"

        norm_path = path.replace("\\", "/").rstrip("/").lower()
        for config in self.settings.settings_data_model.folder_configs:
            cfg_path = config.get("path", "").replace("\\", "/").rstrip("/").lower()
            if norm_path == cfg_path:
                return config.get("icon", "fa5s.folder")

        return "fa5s.folder"

    def load_and_populate(self, folder_path: str, on_complete: callable = None):
        """Loads folders and updates the view."""
        self.folder_view.show_loading_state([folder_path])
        self.file_util.get_files_from_path_async(
            folder_path,
            on_complete=lambda items: self.populate_view(items, on_complete=on_complete)
        )

    def populate_view(self, items: list[FileUtilModel], on_complete: callable = None):
        """Sorts and populates the FolderListView."""
        folder_items = [item for item in items if item.is_dir]

        # Sorting logic moved from FolderList
        if folder_items:
            # Build parent map
            last_at_depth = {}
            # children_map: id(parent) -> list of children
            children_map = {id(None): []}

            for item in folder_items:
                parent = last_at_depth.get(item.depth - 1) if item.depth > 0 else None
                parent_id = id(parent)
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(item)
                last_at_depth[item.depth] = item

            # Sort children
            for parent_id in children_map:
                children_map[parent_id].sort(key=lambda x: x.name.lower())

            # Reconstruct
            sorted_items = []

            def add_sorted_children(parent):
                parent_id = id(parent)
                if parent_id in children_map:
                    for child in children_map[parent_id]:
                        sorted_items.append(child)
                        add_sorted_children(child)

            add_sorted_children(None)
            folder_items = sorted_items

        self.folder_view.clear()
        for item in folder_items:
            icon_name = self._get_icon_for_path(item.full_path)
            self.folder_view.add_folder_item(item, icon_name)

        if on_complete:
            on_complete(items)

    def refresh_icons(self) -> None:
        self.folder_view.refresh_icons(self._get_icon_for_path)
