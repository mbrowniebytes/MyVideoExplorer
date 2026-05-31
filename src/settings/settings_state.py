from pathlib import Path
from PySide6.QtCore import QObject, Signal
from src.utils.json_util import JsonUtil
from src.theme.theme import APP_THEME

# Define configuration paths
CFG_DIR = Path("cfg")
SETTINGS_APP_FILE = CFG_DIR / "settings_app.json"
SETTINGS_UI_FILE = CFG_DIR / "settings_ui.json"
SETTINGS_MEDIA_FILE = CFG_DIR / "settings_media.json"
SETTINGS_FILTER_FILE = CFG_DIR / "settings_filter.json"

DEFAULTS_APP_FILE = CFG_DIR / "defaults_app.json"
DEFAULTS_UI_FILE = CFG_DIR / "defaults_ui.json"
DEFAULTS_MEDIA_FILE = CFG_DIR / "defaults_media.json"
DEFAULTS_FILTER_FILE = CFG_DIR / "defaults_filter.json"


class SettingsState(QObject):
    sig_settings_changed = Signal()

    def __init__(self, log_util) -> None:
        super().__init__()
        self.log_util = log_util
        self.json_util = JsonUtil(self.log_util)
        self.log_level = "info"
        self.folder_configs = []
        self.saved_filters = []
        self._load_settings()
        self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def _ensure_defaults(self):
        """Create cfg directory and defaults split files if they don't exist."""
        if not CFG_DIR.exists():
            CFG_DIR.mkdir(parents=True)

        app_defaults = {
            "log_level": self.log_level,
        }
        ui_defaults = {
            "font_size": 18,
        }
        media_defaults = {
            "folder_configs": self.folder_configs,
        }
        filter_defaults = {
            "saved_filters": self.saved_filters,
        }

        self.json_util.ensure_defaults(CFG_DIR, DEFAULTS_APP_FILE, app_defaults)
        self.json_util.ensure_defaults(CFG_DIR, DEFAULTS_UI_FILE, ui_defaults)
        self.json_util.ensure_defaults(CFG_DIR, DEFAULTS_MEDIA_FILE, media_defaults)
        self.json_util.ensure_defaults(CFG_DIR, DEFAULTS_FILTER_FILE, filter_defaults)

    def _load_settings(self):
        """Load settings from split json files, falling back to split defaults."""
        self._ensure_defaults()

        # Load App Settings
        app_data = self.json_util.load_json(DEFAULTS_APP_FILE)
        app_data.update(self.json_util.load_json(SETTINGS_APP_FILE))

        self.log_level = app_data.get("log_level", self.log_level)

        # Load UI Settings
        ui_data = self.json_util.load_json(DEFAULTS_UI_FILE)
        ui_data.update(self.json_util.load_json(SETTINGS_UI_FILE))

        APP_THEME.font_size = ui_data.get("font_size", APP_THEME.font_size)

        # Load Media Settings
        media_data = self.json_util.load_json(DEFAULTS_MEDIA_FILE)
        media_data.update(self.json_util.load_json(SETTINGS_MEDIA_FILE))
        self.folder_configs = media_data.get("folder_configs", self.folder_configs)

        # Ensure each folder config has an icon
        for config in self.folder_configs:
            if "icon" not in config:
                config["icon"] = "folder"

        # Load Filter Settings
        filter_data = self.json_util.load_json(DEFAULTS_FILTER_FILE)
        filter_data.update(self.json_util.load_json(SETTINGS_FILTER_FILE))
        self.saved_filters = filter_data.get("saved_filters", self.saved_filters)

        # Migration: if saved_filters is a dict, convert it to a list of dicts
        if isinstance(self.saved_filters, dict):
            new_filters = []
            for name, filters in self.saved_filters.items():
                new_filters.append({"name": name, "filters": filters})
            self.saved_filters = new_filters

    def save_app(self):
        """Save only UI tab settings."""
        self._ensure_defaults()

        app_settings = {
            "log_level": self.log_level,
        }

        # Backup then save
        self.json_util.backup_file(SETTINGS_APP_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_APP_FILE, app_settings)

    def save_ui(self):
        """Save only UI tab settings."""
        self._ensure_defaults()

        ui_settings = {
            "font_size": APP_THEME.font_size,
        }

        # Backup then save
        self.json_util.backup_file(SETTINGS_UI_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_UI_FILE, ui_settings)

    def save_media(self):
        """Save only Media tab settings."""
        self._ensure_defaults()

        media_settings = {
            "folder_configs": self.folder_configs,
        }

        # Backup then save
        self.json_util.backup_file(SETTINGS_MEDIA_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_MEDIA_FILE, media_settings)

    def save_filters(self):
        """Save only Filters tab settings."""
        self._ensure_defaults()

        filter_settings = {
            "saved_filters": self.saved_filters,
        }

        # Backup then save
        self.json_util.backup_file(SETTINGS_FILTER_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_FILTER_FILE, filter_settings)

    def load_app(self):
        """Reload App settings from file."""
        app_data = self.json_util.load_json(DEFAULTS_APP_FILE)
        app_data.update(self.json_util.load_json(SETTINGS_APP_FILE))
        self.log_level = app_data.get("log_level", self.log_level)

    def load_media(self):
        """Reload Media settings from file."""
        media_data = self.json_util.load_json(DEFAULTS_MEDIA_FILE)
        media_data.update(self.json_util.load_json(SETTINGS_MEDIA_FILE))
        self.folder_configs = media_data.get("folder_configs", self.folder_configs)
        # Ensure each folder config has an icon
        for config in self.folder_configs:
            if "icon" not in config:
                config["icon"] = "folder"

    def load_filters(self):
        """Reload Filter settings from file."""
        filter_data = self.json_util.load_json(DEFAULTS_FILTER_FILE)
        filter_data.update(self.json_util.load_json(SETTINGS_FILTER_FILE))
        self.saved_filters = filter_data.get("saved_filters", self.saved_filters)
        # Migration: if saved_filters is a dict, convert it to a list of dicts
        if isinstance(self.saved_filters, dict):
            new_filters = []
            for name, filters in self.saved_filters.items():
                new_filters.append({"name": name, "filters": filters})
            self.saved_filters = new_filters


    def save_filter(self, name: str, filter_cfg: list[dict]) -> None:
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
        self.sig_settings_changed.emit()

    def delete_filter(self, name: str) -> None:
        """Deletes a named filter configuration."""
        self.saved_filters = [f for f in self.saved_filters if f.get("name") != name]
        self.save_filters()
        self.sig_settings_changed.emit()

    def save_settings(self):
        """Save all tabs' settings (legacy method for backward compatibility)."""
        self.save_app()
        self.save_ui()
        self.save_media()
        self.save_filters()
