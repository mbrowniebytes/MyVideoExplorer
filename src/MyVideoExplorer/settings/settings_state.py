from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.utils.json_util import JsonUtil
from MyVideoExplorer.theme.theme import APP_THEME

# Define configuration paths
CFG_DIR = Path("cfg")
SETTINGS_STATE_FILE = CFG_DIR / "settings_state.json"
SETTINGS_APP_FILE = CFG_DIR / "settings_app.json"
SETTINGS_UI_FILE = CFG_DIR / "settings_ui.json"
SETTINGS_MEDIA_FILE = CFG_DIR / "settings_media.json"
SETTINGS_FILTER_FILE = CFG_DIR / "settings_filter.json"

DEFAULTS_STATE_FILE = CFG_DIR / "defaults_state.json"
DEFAULTS_APP_FILE = CFG_DIR / "defaults_app.json"
DEFAULTS_UI_FILE = CFG_DIR / "defaults_ui.json"
DEFAULTS_MEDIA_FILE = CFG_DIR / "defaults_media.json"
DEFAULTS_FILTER_FILE = CFG_DIR / "defaults_filter.json"


class SettingsState(QObject):
    sig_settings_changed = Signal(object)
    sig_window_size_changed = Signal(object)
    sig_window_pos_changed = Signal(object)

    def __init__(self, log_util: Any) -> None:
        super().__init__()

        self.log_util = log_util
        self.json_util = JsonUtil(self.log_util)

        self.prior_folder = ""
        self.app_pos = ""
        self.app_size = ""

        self.auto_select_folder = "auto_select_prior_folder"
        self.log_level = "info"
        self.launch_app_size = "app_size_min"
        self.launch_app_pos = "app_pos_center_center"

        self.folder_configs: list[dict[str, Any]] = []
        self.saved_filters: list[dict[str, Any]] = []
        self._load_settings()
        self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def _ensure_defaults(self) -> None:
        """Create cfg directory and defaults split files if they don't exist."""
        if not CFG_DIR.exists():
            CFG_DIR.mkdir(parents=True)

        state_defaults: dict[str, str] = {
            "prior_folder": "",
            "app_pos": "",
            "app_size": "",
        }
        app_defaults: dict[str, str | bool] = {
            "log_level": self.log_level,
            "auto_select_folder": self.auto_select_folder,
            "launch_app_size": self.launch_app_size,
            "launch_app_pos": self.launch_app_pos,
        }
        ui_defaults: dict[str, int | str] = {
            "font_size": 18,
            "app_font": "Lato",
        }
        media_defaults: dict[str, list[dict[str, Any]]] = {
            "folder_configs": self.folder_configs,
        }
        filter_defaults: dict[str, list[dict[str, Any]]] = {
            "saved_filters": self.saved_filters,
        }

        self.json_util.ensure_defaults(CFG_DIR, DEFAULTS_STATE_FILE, state_defaults)
        self.json_util.ensure_defaults(CFG_DIR, DEFAULTS_APP_FILE, app_defaults)
        self.json_util.ensure_defaults(CFG_DIR, DEFAULTS_UI_FILE, ui_defaults)
        self.json_util.ensure_defaults(CFG_DIR, DEFAULTS_MEDIA_FILE, media_defaults)
        self.json_util.ensure_defaults(CFG_DIR, DEFAULTS_FILTER_FILE, filter_defaults)

    def _load_settings(self) -> None:
        """Load settings from split json files, falling back to split defaults."""
        self._ensure_defaults()

        # Load State Settings
        state_data = self.json_util.load_json(DEFAULTS_STATE_FILE)
        if SETTINGS_STATE_FILE.exists():
            state_data.update(self.json_util.load_json(SETTINGS_STATE_FILE))

        self.prior_folder = state_data.get("prior_folder", "")
        self.app_size = state_data.get("app_size", "")
        self.app_pos = state_data.get("app_pos", "")

        # Load App Settings
        app_data = self.json_util.load_json(DEFAULTS_APP_FILE)
        if SETTINGS_APP_FILE.exists():
            app_data.update(self.json_util.load_json(SETTINGS_APP_FILE))

        self.log_level = app_data.get("log_level", self.log_level)
        self.auto_select_folder = app_data.get(
            "auto_select_folder", "auto_select_prior_folder"
        )
        self.launch_app_size = app_data.get("launch_app_size", "app_size_min")
        self.launch_app_pos = app_data.get("launch_app_pos", "app_pos_center_center")

        # Load UI Settings
        ui_data = self.json_util.load_json(DEFAULTS_UI_FILE)
        if SETTINGS_UI_FILE.exists():
            ui_data.update(self.json_util.load_json(SETTINGS_UI_FILE))

        APP_THEME.font_size = ui_data.get("font_size", APP_THEME.font_size)
        APP_THEME.font_family = ui_data.get("app_font", APP_THEME.font_family)

        # Load Media Settings
        media_data = self.json_util.load_json(DEFAULTS_MEDIA_FILE)
        if SETTINGS_MEDIA_FILE.exists():
            media_data.update(self.json_util.load_json(SETTINGS_MEDIA_FILE))
        self.folder_configs = media_data.get("folder_configs", self.folder_configs)

        # Ensure each folder config has an icon
        for config in self.folder_configs:
            if "icon" not in config:
                config["icon"] = "folder"

        # Load Filter Settings
        filter_data = self.json_util.load_json(DEFAULTS_FILTER_FILE)
        if SETTINGS_FILTER_FILE.exists():
            filter_data.update(self.json_util.load_json(SETTINGS_FILTER_FILE))
        self.saved_filters = filter_data.get("saved_filters", self.saved_filters)

        # Migration: if saved_filters is a dict, convert it to a list of dicts
        if isinstance(self.saved_filters, dict):
            new_filters: list[dict[str, Any]] = []
            for name, filters in self.saved_filters.items():
                new_filters.append({"name": name, "filters": filters})
            self.saved_filters = new_filters

    def save_state(self, settings:dict[str, str]) -> None:
        """Save only App tab settings."""
        self._ensure_defaults()

        state_settings: dict[str, str] = {
            "prior_folder": settings.get("prior_folder", ""),
            "app_size": settings.get("app_size", ""),
            "app_pos": settings.get("app_pos", ""),
        }

        # Backup then save
        self.json_util.backup_file(SETTINGS_STATE_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_STATE_FILE, state_settings)

    def save_app(self) -> None:
        """Save only App tab settings."""
        self._ensure_defaults()

        app_settings: dict[str, str | bool] = {
            "log_level": self.log_level,
            "auto_select_folder": self.auto_select_folder,
            "launch_app_size": self.launch_app_size,
            "launch_app_pos": self.launch_app_pos,
        }

        # Backup then save
        self.json_util.backup_file(SETTINGS_APP_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_APP_FILE, app_settings)

    def save_ui(self) -> None:
        """Persist UI settings to file."""
        self._ensure_defaults()

        settings_data = {
            "font_size": APP_THEME.font_size,
            "app_font": APP_THEME.font_family,
        }

        # Backup then save
        self.json_util.backup_file(SETTINGS_UI_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_UI_FILE, settings_data)

    def save_media(self) -> None:
        """Save only Media tab settings."""
        self._ensure_defaults()

        media_settings: dict[str, list[dict[str, Any]]] = {
            "folder_configs": self.folder_configs,
        }

        # Backup then save
        self.json_util.backup_file(SETTINGS_MEDIA_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_MEDIA_FILE, media_settings)

    def save_filters(self) -> None:
        """Save only Filters tab settings."""
        self._ensure_defaults()

        filter_settings: dict[str, list[dict[str, Any]]] = {
            "saved_filters": self.saved_filters,
        }

        # Backup then save
        self.json_util.backup_file(SETTINGS_FILTER_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_FILTER_FILE, filter_settings)

        self.sig_settings_changed.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Filter settings were saved.",
                flow=SignalFlow.COMPONENT_INTERACTION,
            )
        )

    def load_ui(self) -> None:
        """Reload UI settings from file."""
        ui_data = self.json_util.load_json(DEFAULTS_UI_FILE)
        if SETTINGS_UI_FILE.exists():
            ui_data.update(self.json_util.load_json(SETTINGS_UI_FILE))

        APP_THEME.font_size = ui_data.get("font_size", APP_THEME.font_size)
        APP_THEME.font_family = ui_data.get("app_font", APP_THEME.font)

    def load_app(self) -> None:
        """Reload App settings from file."""
        app_data = self.json_util.load_json(DEFAULTS_APP_FILE)
        if SETTINGS_APP_FILE.exists():
            app_data.update(self.json_util.load_json(SETTINGS_APP_FILE))
        self.log_level = app_data.get("log_level", self.log_level)
        self.auto_select_folder = app_data.get(
            "auto_select_folder", "auto_select_prior_folder"
        )
        self.launch_app_size = app_data.get("launch_app_size", "app_size_min")
        self.launch_app_pos = app_data.get("launch_app_pos", "app_pos_last")

    def load_media(self) -> None:
        """Reload Media settings from file."""
        media_data = self.json_util.load_json(DEFAULTS_MEDIA_FILE)
        if SETTINGS_MEDIA_FILE.exists():
            media_data.update(self.json_util.load_json(SETTINGS_MEDIA_FILE))
        self.folder_configs = media_data.get("folder_configs", self.folder_configs)
        # Ensure each folder config has an icon
        for config in self.folder_configs:
            if "icon" not in config:
                config["icon"] = "folder"

    def load_filters(self) -> None:
        """Reload Filter settings from file."""
        filter_data = self.json_util.load_json(DEFAULTS_FILTER_FILE)
        if SETTINGS_FILTER_FILE.exists():
            filter_data.update(self.json_util.load_json(SETTINGS_FILTER_FILE))
        self.saved_filters = filter_data.get("saved_filters", self.saved_filters)
        # Migration: if saved_filters is a dict, convert it to a list of dicts
        if isinstance(self.saved_filters, dict):
            new_filters = []
            for name, filters in self.saved_filters.items():
                new_filters.append({"name": name, "filters": filters})
            self.saved_filters = new_filters


    def save_filter(self, name: str, filter_cfg: list[dict[str, Any]]) -> None:
        """Saves a named filter configuration."""
        # Check if filter with this name already exists
        b_found = False
        for i, saved_filter_cfg in enumerate(self.saved_filters):
            if saved_filter_cfg.get("name") == name:
                self.saved_filters[i] = {"name": name, "filters": filter_cfg}
                b_found = True
                break

        if not b_found:
            self.saved_filters.append({"name": name, "filters": filter_cfg})

        self.save_filters()
        self.sig_settings_changed.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Filter settings were changed.",
                flow=SignalFlow.COMPONENT_INTERACTION,
            )
        )

    def delete_filter(self, name: str) -> None:
        """Deletes a named filter configuration."""
        self.saved_filters = [f for f in self.saved_filters if f.get("name") != name]
        self.save_filters()
        self.sig_settings_changed.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Filter settings were deleted.",
                flow=SignalFlow.COMPONENT_INTERACTION,
            )
        )

    def save_settings(self) -> None:
        """Save all tabs' settings (legacy method for backward compatibility)."""
        self.save_app()
        self.save_ui()
        self.save_media()
        self.save_filters()
