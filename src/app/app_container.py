from pathlib import Path
from src.app.app_controller import AppController
from src.app.app_signals import SignalRegistry
from src.file_list.file_list import FileList
from src.folder_list.folder_list import FolderList
from src.folder_nav.folder_nav import FolderNav
from src.folder_filter.folder_filter import FolderFilters
from src.folder_filter.folder_filter_filter import FolderFilterFilter
from src.image_list.image_list import ImageList
from src.image_list.image_list_view import ImageListView
from src.media_info.media_info import MediaInfo
from src.media_info_side.media_info_side_view import MediaInfoSideView
from src.media_info.media_info_view import MediaInfoView
from src.media_info_tabs.media_info_tabs import MediaInfoTabs
from src.settings.settings import Settings
from src.utils.log_util import LogUtil
from src.utils.file_util import FileUtil
from src.utils.file_util_model import FileUtilModel
from src.utils.nfo_parse_util import NfoParseUtil
from src.utils.str_util import StrUtil
from src.utils.json_util import JsonUtil
from src.video_player.video_player import VideoPlayer


class AppContainer:
    """
    Composition root: instantiates all components and wires signals.
    Separates CONSTRUCTION from LAYOUT (which stays in App.build()).
    """

    def __init__(self) -> None:
        # Load saved log level
        log_util = LogUtil().configure("error")
        self.log_util = log_util  # Set early so available even if initialization fails

        try:
            json_util = JsonUtil(log_util)
            cfg_dir = Path("cfg")
            defaults_app_file = cfg_dir / "defaults_app.json"
            settings_app_file = cfg_dir / "settings_app.json"
            app_data = json_util.load_json(defaults_app_file)
            app_data.update(json_util.load_json(settings_app_file))
            log_level = app_data.get("log_level", "error")

            self.log_util = log_util.configure(log_level)
            self.log_util.log_memory("Application starting...")
        except Exception as e:
            self.log_util.error(f"Error loading configuration: {e}")
            raise

        try:
            self.settings = Settings(self.log_util)
        except Exception as e:
            self.log_util.error(f"Error initializing Settings: {e}")
            raise

        try:
            self.json_util = JsonUtil(self.log_util)
            self.file_util = FileUtil(self.log_util)
            self.nfo_parse_util = NfoParseUtil(self.file_util, self.log_util)
            self.str_util = StrUtil(self.log_util)

            self.signals = SignalRegistry()
            self.controller = AppController(self.log_util, self.signals)

            self.folder_nav_filters_filter = FolderFilterFilter(
                self.nfo_parse_util, self.settings.settings_data_model.folder_configs, self.log_util
            )
            self.folder_list = FolderList(self.file_util, self.settings, self.log_util)

            self.folder_nav_filters = FolderFilters(
                self.folder_nav_filters_filter, self.file_util, self.settings, self.log_util
            )
            self.folder_nav = FolderNav(self.folder_nav_filters, self.log_util)
            self.file_list = FileList(self.file_util, self.log_util)

            self.media_info_view = MediaInfoView(self.nfo_parse_util, self.str_util, self.log_util)
            self.media_info_side_view = MediaInfoSideView(
                self.nfo_parse_util, self.str_util, self.log_util
            )
            self.media_info = MediaInfo(
                self.media_info_view, self.media_info_side_view, self.log_util
            )

            self.image_list_view = ImageListView(
                self.str_util, self.media_info_side_view, self.file_list, self.log_util
            )
            self.image_list = ImageList(
                self.file_util,
                self.nfo_parse_util,
                self.str_util,
                self.image_list_view,
                self.file_list,
                self.log_util,
            )

            self.video_player = VideoPlayer(self.file_util, self.log_util)

            self.media_info_tabs = MediaInfoTabs(self.log_util)

            self._wire_all_signals()
        except Exception as e:
            self.log_util.error(f"Error during component initialization: {e}", extra_info={"component_error": str(e)})
            raise

    def _wire_all_signals(self) -> None:
        """
        Single place where all signal connections happen.
        No dynamic event-handler assignment belongs here.
        """
        self._wire_user_inputs()
        self._wire_controller_outputs()
        self._wire_component_interactions()

    def _wire_user_inputs(self) -> None:
        """User interactions → Controller state."""
        self.folder_nav.sig_root_folder.connect(lambda p: self.controller.set_root_folders(p.data))
        self.folder_nav.sig_selected_folder.connect(lambda p: self.controller.set_current_folder(p.data))

        self.folder_list.sig_folder_selected_intent.connect(
            lambda p: self.controller.set_current_folder(p.data)
        )

        self.file_list.sig_file_selected_intent.connect(
            lambda payload: self.controller.set_current_file(payload.data)
        )

        self.image_list.sig_image_selected_intent.connect(
            lambda p: self.controller.set_current_file(p.data)
        )

        self.media_info_tabs.sig_tab_selection_changed.connect(self.controller.set_current_tab)

        self.settings.media_settings_tab.sig_changed.connect(lambda p: self.folder_list.refresh_icons())
        self.settings.media_settings_tab.sig_root_folders_changed.connect(lambda p: self.controller.set_root_folders(p.data))
        self.folder_nav_filters.sig_loading_started.connect(self.folder_list.show_loading_state)


    def _wire_controller_outputs(self) -> None:
        """Controller state changes → Component refreshes."""
        # self.signals.sig_root_folder.connect(lambda p: self._on_set_root_folder(p.data))
        # New: handle list of root folders so FolderNav can display all roots
        self.signals.sig_root_folders.connect(lambda p: self.folder_nav.set_root_folders(p.data))

        self.signals.sig_selected_folder.connect(lambda p: self._on_folder_selected(p.data))

        self.signals.sig_file_changed.connect(lambda p: self.file_list.set_selected_file(p.data))
        self.signals.sig_file_changed.connect(lambda p: self.media_info.set_image_path(p.data))
        self.signals.sig_file_changed.connect(lambda p: self.image_list.update_image_from_item(p.data))

        self.signals.sig_image_changed.connect(lambda p: self.image_list.set_selected_image(p.data))

        self.signals.sig_tab_changed.connect(lambda p: self._on_tab_changed(p.data))

        self.settings.settings_data_model.sig_settings_changed.connect(lambda p: self.folder_list.refresh_icons())
        # When media folders are deleted in settings, update controller root_folders
        if hasattr(self.settings, "media_tab") and hasattr(self.settings.media_tab, "sig_root_folders_changed"):
            self.settings.media_tab.sig_root_folders_changed.connect(lambda p: self.controller.set_root_folders(p.data))

    def _wire_component_interactions(self) -> None:
        """Component-to-component interactions (local, not via controller)."""
        self.image_list.sig_wheel_step.connect(lambda p: self.folder_list.select_next_folder(p.data))
        self.image_list.sig_right_click.connect(lambda p: self.image_list.request_next_image())

        self.image_list.sig_double_click.connect(lambda p: self._play_video_from_current_folder())
        self.media_info.sig_play_video.connect(lambda p: self._play_video_from_current_folder())

        self.folder_nav.sig_selected_items.connect(lambda p: self._on_filtered_items(p.data))

    def _on_tab_changed(self, tab_index: int) -> None:
        """Bridge: translate controller signal to component method."""
        self.media_info.refresh(self.controller.state.current_folder, tab_index)

    def _play_video_from_current_folder(self) -> None:
        self.video_player.set_folder_path(self.controller.state.current_folder)
        self.video_player.play_video()

    def _on_filtered_items(self, items: list[FileUtilModel]) -> None:
        self.folder_list.populate_view(items)

    # def _on_set_root_folder(self, folder_path: str) -> None:
    #     # print(f"_on_set_root_folder:{folder_path}")
    #     self.folder_nav.set_root_folder([folder_path])
    #     self.folder_list.refresh(folder_path, force=True)

    def _on_folder_selected(self, folder_path: str) -> None:
        # We still want to avoid circular updates if everything is already in sync
        if (
            self.folder_list.folder_view.property("last_selected_folder") == folder_path
            and self.controller.state.current_folder == folder_path
            and self.media_info.folder_path == folder_path
        ):
            return

        self.folder_list.folder_view.setProperty("last_selected_folder", folder_path)
        # print(f"_on_folder_selected:{folder_path}")

        self.folder_list.set_selected_folder(folder_path)

        self.file_list.refresh(folder_path)
        self.image_list.refresh(folder_path)

        self.video_player.set_folder_path(folder_path)
        self.media_info.refresh(folder_path, self.controller.state.current_tab)
