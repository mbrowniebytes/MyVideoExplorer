from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMainWindow

from MyVideoExplorer.app.app_controller import AppController
from MyVideoExplorer.app.app_signals import SignalRegistry
from MyVideoExplorer.file_list.file_list import FileList
from MyVideoExplorer.folder_filter.folder_filter import FolderFilters
from MyVideoExplorer.folder_filter.folder_filter_filter import FolderFilterFilter
from MyVideoExplorer.folder_list.folder_list import FolderList
from MyVideoExplorer.folder_nav.folder_nav import FolderNav
from MyVideoExplorer.image_list.image_list import ImageList
from MyVideoExplorer.image_list.image_list_view import ImageListView
from MyVideoExplorer.media_info.media_info import MediaInfo
from MyVideoExplorer.media_info.media_info_view import MediaInfoView
from MyVideoExplorer.media_info_side.media_info_side_view import MediaInfoSideView
from MyVideoExplorer.media_info_tabs.media_info_tabs import MediaInfoTabs
from MyVideoExplorer.settings.settings import Settings
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.font_util import FontUtil
from MyVideoExplorer.utils.json_util import JsonUtil
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.utils.str_util import StrUtil
from MyVideoExplorer.video_player.video_player import VideoPlayer


DEFAULT_WINDOW_SIZE = (1200, 700)
MIN_WINDOW_SIZE = (1000, 500)


class AppContainer:
    """
    Composition root: instantiates all components and wires signals.
    Separates CONSTRUCTION from LAYOUT (which stays in App.build()).
    """

    def __init__(self, window: QMainWindow) -> None:
        self.window = window
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
            self.file_util = FileUtil(self.log_util)
            self.settings = Settings(self.log_util, self.file_util)
        except Exception as e:
            self.log_util.error(f"Error initializing Settings: {e}")
            raise

        try:
            self.json_util = JsonUtil(self.log_util)
            self.nfo_parse_util = NfoParseUtil(self.file_util, self.log_util)
            self.str_util = StrUtil(self.log_util)
            self.font_util = FontUtil(self.log_util, self.file_util)

            self.signals = SignalRegistry()
            self.controller = AppController(self.log_util, self.signals)

            self.folder_nav_filters_filter = FolderFilterFilter(
                self.nfo_parse_util,
                self.settings.settings_data_model,
                self.log_util,
            )
            self.folder_list = FolderList(self.file_util, self.settings, self.log_util)
            self.folder_list.setParent(self.window)

            self.folder_nav_filters = FolderFilters(
                self.folder_nav_filters_filter,
                self.file_util,
                self.settings,
                self.log_util,
            )
            self.folder_nav_filters.setParent(self.window)
            self.folder_nav = FolderNav(self.folder_nav_filters, self.log_util)
            self.folder_nav.setParent(self.window)
            self.file_list = FileList(self.file_util, self.log_util)
            self.file_list.setParent(self.window)

            self.media_info_view = MediaInfoView(
                self.nfo_parse_util, self.str_util, self.log_util
            )
            self.media_info_view.setParent(self.window)
            self.media_info_side_view = MediaInfoSideView(
                self.nfo_parse_util, self.str_util, self.log_util
            )
            self.media_info_side_view.setParent(self.window)
            self.media_info = MediaInfo(
                self.media_info_view, self.media_info_side_view, self.log_util
            )
            self.media_info.setParent(self.window)

            self.image_list_view = ImageListView(
                self.str_util, self.media_info_side_view, self.file_list, self.log_util
            )
            self.image_list_view.setParent(self.window)
            self.image_list = ImageList(
                self.file_util,
                self.settings,
                self.nfo_parse_util,
                self.str_util,
                self.image_list_view,
                self.file_list,
                self.log_util,
            )
            self.image_list.setParent(self.window)

            self.video_player = VideoPlayer(self.file_util, self.log_util)

            self.media_info_tabs = MediaInfoTabs(
                self.log_util,
                media_info=self.media_info,
                image_list=self.image_list,
                settings=self.settings,
            )
            self.media_info_tabs.setParent(self.window)

            self._wire_all_signals()

            # Apply saved launch size and position immediately so the app opens
            # using the user's preferred settings (if present).
            try:
                self.resize_window(
                    self.window,
                    app_size=self.settings.settings_data_model.launch_app_size,
                    app_pos=self.settings.settings_data_model.launch_app_pos,
                    apply_resize=True,
                )
            except Exception as e:
                self.log_util.debug(f"Failed applying initial window size/pos: {e}")
        except Exception as e:
            self.log_util.error(
                f"Error during component initialization: {e}",
                extra_info={"component_error": str(e)},
            )
            raise


    def _wire_all_signals(self) -> None:
        """
        Single place where all signal connections happen.
        No dynamic event-handler assignment belongs here.
        """
        self._wire_user_inputs()
        self._wire_controller_outputs()
        self._wire_component_interactions()

    @staticmethod
    def _connect(signal, slot) -> None:
        signal.connect(slot)

    def _wire_user_inputs(self) -> None:
        """User interactions → Controller state."""
        self._connect(self.folder_nav.root_folder_changed, lambda p: self.controller.set_root_folders(p.data))
        self._connect(self.folder_nav.selected_folder_changed, lambda p: self.controller.set_current_folder(p.data))
        self._connect(self.folder_list.folder_selected_intent, lambda p: self.controller.set_current_folder(p.data))
        self._connect(self.folder_list.folder_navigation_requested, lambda p: self.controller.set_current_folder(p.data))
        self._connect(self.file_list.file_selected_intent, lambda payload: self.controller.set_current_file(payload.data))
        self._connect(self.image_list.image_selected_intent, lambda p: self.controller.set_current_file(p.data))
        self._connect(self.media_info_tabs.tab_selection_changed, self.controller.set_current_tab)
        self._connect(self.settings.media_settings_tab.changed, lambda p: self.folder_list.refresh_icons())
        self._connect(self.settings.media_settings_tab.root_folders_changed, lambda p: self.controller.set_root_folders(p.data))
        self._connect(self.folder_nav_filters.loading_started, self.folder_list.show_loading_state)

    def _wire_controller_outputs(self) -> None:
        """Controller state changes → Component refreshes."""
        self._connect(self.signals.root_folders_changed, lambda p: self.folder_nav.set_root_folders(p.data))
        self._connect(self.signals.selected_folder_changed, lambda p: self._on_folder_selected(p.data))
        self._connect(self.signals.file_changed, lambda p: self.file_list.set_selected_file(p.data))
        self._connect(self.signals.file_changed, lambda p: self.media_info.set_image_path(p.data))
        self._connect(self.signals.file_changed, lambda p: self.image_list.update_image_from_item(p.data))
        self._connect(self.signals.image_changed, lambda p: self.image_list.set_selected_image(p.data))
        self._connect(self.signals.tab_changed, lambda p: self._on_tab_changed(p.data))
        self._connect(self.settings.settings_data_model.settings_changed, lambda p: self.folder_list.refresh_icons())
        self._connect(self.settings.settings_data_model.window_size_changed, lambda p: self.resize_window(self.window, p.data))
        self._connect(self.settings.settings_data_model.window_pos_changed, lambda p: self.resize_window(self.window, app_pos=p.data))
        self._connect(self.settings.media_settings_tab.root_folders_changed, lambda p: self.controller.set_root_folders(p.data))

    def _wire_component_interactions(self) -> None:
        """Component-to-component interactions (local, not via controller)."""
        self._connect(self.image_list.wheel_step, lambda p: self.folder_list.select_next_folder(p.data))
        self._connect(self.image_list.context_menu_requested, lambda p: self.image_list.request_next_image())
        self._connect(self.image_list.double_click_requested, lambda p: self._play_video_from_current_folder())
        self._connect(self.media_info.play_video_requested, lambda p: self._play_video_from_current_folder())
        self._connect(self.folder_nav.filtered_items_updated, lambda p: self._on_filtered_items(p.data))

    def _on_tab_changed(self, tab_index: int) -> None:
        """Bridge: translate controller signal to component method."""
        self.media_info.refresh(self.controller.state.current_folder, tab_index)

    def _play_video_from_current_folder(self) -> None:
        self.video_player.set_folder_path(self.controller.state.current_folder)
        self.video_player.play_video()

    def _on_filtered_items(self, items: list[FileUtilModel]) -> None:
        self.folder_list.populate_view(items)

        if items:
            first_item = items[0]
            auto_select_folder = self.settings.settings_data_model.auto_select_folder
            prior_folder = self.settings.settings_data_model.prior_folder
            self.log_util.debug(
                "Auto-selecting folder after filters change",
                extra_info={
                    "auto_select_folder": auto_select_folder,
                    "prior_folder": prior_folder,
                    "first_item": first_item,
                },
            )

            if auto_select_folder == "auto_select_prior_folder" and prior_folder:
                self.controller.set_current_folder(prior_folder, force=True)
            else:
                self.controller.set_current_folder(first_item.full_path, force=True)
        else:
            self.image_list.update_image_from_folder("")

    def _on_folder_selected(self, folder_path: str) -> None:
        if (
            self.folder_list.folder_list_view.property("last_selected_folder")
            == folder_path
            and self.controller.state.current_folder == folder_path
            and self.media_info.folder_path == folder_path
        ):
            return

        self.folder_list.folder_list_view.setProperty(
            "last_selected_folder", folder_path
        )
        self.log_util.debug(
            "Folder selected",
            extra_info={"folder_path": folder_path},
        )

        self.folder_list.set_selected_folder(folder_path)
        self.file_list.refresh(folder_path)
        self.image_list.refresh(folder_path)

        if self.image_list.selected_image_path:
            self.file_list.set_selected_file(self.image_list.selected_image_path)

        self.video_player.set_folder_path(folder_path)
        self.media_info.refresh(folder_path, self.controller.state.current_tab)

    @staticmethod
    def _parse_window_size(value: str) -> tuple[int, int] | None:
        """Parse sizes like '1600x900' or names like 'app_size_1600x900'.

        Returns (width, height) or None on failure.
        """
        if not value or "x" not in value:
            return None

        # Allow values that include a prefix such as 'app_size_1600x900'
        if value.startswith("app_size_"):
            value = value.split("app_size_", 1)[1]

        try:
            width, height = map(int, value.split("x", 1))
        except ValueError:
            return None
        return width, height

    def _apply_window_size(self, window: QMainWindow, launch_size: str) -> None:
        if launch_size == "app_size_maximized":
            window.showMaximized()
            return

        if launch_size == "app_size_last" and self.settings.settings_data_model.app_size:
            launch_size = self.settings.settings_data_model.app_size

        parsed_size = self._parse_window_size(launch_size)
        if parsed_size is not None:
            width, height = parsed_size
            width = max(width, MIN_WINDOW_SIZE[0])
            height = max(height, MIN_WINDOW_SIZE[1])
            self.log_util.info(
                "Applying window size",
                extra_info={"width": width, "height": height},
            )
            window.resize(width, height)
            return

        window.resize(*DEFAULT_WINDOW_SIZE)

    def _apply_window_position(self, window: QMainWindow, launch_pos: str) -> None:
        if launch_pos == "app_pos_last" and self.settings.settings_data_model.app_pos:
            app_pos_coords = self.settings.settings_data_model.app_pos
            if app_pos_coords and "," in app_pos_coords:
                try:
                    x, y = map(int, app_pos_coords.split(",", 1))
                    window.move(x, y)
                except ValueError:
                    pass
                return

        if not launch_pos.startswith("app_pos_center"):
            return

        screen = QGuiApplication.primaryScreen().availableGeometry()
        window_geo = window.frameGeometry()

        if launch_pos == "app_pos_center_center":
            x = screen.left() + (screen.width() - window_geo.width()) // 2
            y = screen.top() + (screen.height() - window_geo.height()) // 2
            window.move(x, y)
        elif launch_pos == "app_pos_center_bottom":
            x = screen.left() + (screen.width() - window_geo.width()) // 2
            y = screen.top() + screen.height() - window_geo.height()
            window.move(x, y)
        elif launch_pos == "app_pos_center_top":
            x = screen.left() + (screen.width() - window_geo.width()) // 2
            y = screen.top()
            window.move(x, y)

    def resize_window(
        self,
        window: QMainWindow | None,
        app_size: str = "",
        app_pos: str = "",
        apply_resize: bool = True,
    ) -> None:
        if not window:
            self.log_util.warn("resize_window called without a window object")
            return

        self.window = window

        if apply_resize:
            launch_size = self.settings.settings_data_model.launch_app_size
            if app_size:
                launch_size = app_size
            self._apply_window_size(window, launch_size)

        launch_pos = self.settings.settings_data_model.launch_app_pos
        if app_pos:
            launch_pos = app_pos
        self._apply_window_position(window, launch_pos)
