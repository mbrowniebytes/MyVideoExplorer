import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.utils.json_util import JsonUtil
from MyVideoExplorer.theme.theme import APP_THEME

# Use a package-local defaults directory so built-in defaults are versioned with
# the application instead of living only at the repo root. Runtime user settings
# still live in the working-directory cfg folder for easy local editing.
PACKAGE_CFG_DIR = Path(__file__).resolve().parent / "cfg"
CFG_DIR = Path("cfg")
SETTINGS_STATE_FILE = CFG_DIR / "settings_state.json"
SETTINGS_APP_FILE = CFG_DIR / "settings_app.json"
SETTINGS_UI_FILE = CFG_DIR / "settings_ui.json"
SETTINGS_MEDIA_FILE = CFG_DIR / "settings_media.json"
SETTINGS_FILTER_FILE = CFG_DIR / "settings_filter.json"

DEFAULTS_STATE_FILE = PACKAGE_CFG_DIR / "defaults_state.json"
DEFAULTS_APP_FILE = PACKAGE_CFG_DIR / "defaults_app.json"
DEFAULTS_UI_FILE = PACKAGE_CFG_DIR / "defaults_ui.json"
DEFAULTS_MEDIA_FILE = PACKAGE_CFG_DIR / "defaults_media.json"
DEFAULTS_FILTER_FILE = PACKAGE_CFG_DIR / "defaults_filter.json"


class SettingsState(QObject):
    settings_changed = Signal(object)
    window_size_changed = Signal(object)
    window_pos_changed = Signal(object)

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
        self.show_loading_screen = True

        self.media_configs: list[dict[str, Any]] = []
        self._db_enabled = True
        self.saved_filters: list[dict[str, Any]] = []
        self._load_settings()
        self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def _ensure_defaults(self) -> None:
        """Create user settings dir and package defaults if they don't exist."""
        if not CFG_DIR.exists():
            CFG_DIR.mkdir(parents=True)
        PACKAGE_CFG_DIR.mkdir(parents=True, exist_ok=True)

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
            "show_loading_screen": self.show_loading_screen,
        }
        ui_defaults: dict[str, int | str] = {
            "font_size": 18,
            "app_font": "Lato",
        }
        media_defaults: dict[str, Any] = {
            "media_configs": self.media_configs,
            "db_enabled": self._db_enabled,
        }
        filter_defaults: dict[str, list[dict[str, Any]]] = {
            "saved_filters": self.saved_filters,
        }

        self.json_util.ensure_defaults(PACKAGE_CFG_DIR, DEFAULTS_STATE_FILE, state_defaults)
        self.json_util.ensure_defaults(PACKAGE_CFG_DIR, DEFAULTS_APP_FILE, app_defaults)
        self.json_util.ensure_defaults(PACKAGE_CFG_DIR, DEFAULTS_UI_FILE, ui_defaults)
        self.json_util.ensure_defaults(PACKAGE_CFG_DIR, DEFAULTS_MEDIA_FILE, media_defaults)
        self.json_util.ensure_defaults(PACKAGE_CFG_DIR, DEFAULTS_FILTER_FILE, filter_defaults)

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
        self.show_loading_screen = app_data.get("show_loading_screen", True)

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
        self.media_configs = media_data.get("media_configs", self.media_configs)
        self._db_enabled = media_data.get("db_enabled", False)

        # Ensure each folder config has an icon
        for config in self.media_configs:
            if "icon" not in config:
                config["icon"] = "fa6s.folder"

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
            "show_loading_screen": self.show_loading_screen,
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

        media_settings: dict[str, Any] = {
            "media_configs": self.media_configs,
            "db_enabled": self._db_enabled,
        }

        self.log_util.info(f"Saving media_settings: {media_settings}")
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

        self.settings_changed.emit(
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
        APP_THEME.font_family = ui_data.get("app_font", APP_THEME.font_family)

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
        self.show_loading_screen = app_data.get("show_loading_screen", True)

    def load_media(self) -> None:
        """Reload Media settings from file."""
        media_data = self.json_util.load_json(DEFAULTS_MEDIA_FILE)
        if SETTINGS_MEDIA_FILE.exists():
            media_data.update(self.json_util.load_json(SETTINGS_MEDIA_FILE))
        self.media_configs = media_data.get("media_configs", self.media_configs)
        self.log_util.info(f"Loaded media_configs: {self.media_configs}")
        self._db_enabled = media_data.get("db_enabled", True)
        # Ensure each folder config has an icon
        for config in self.media_configs:
            if "icon" not in config:
                config["icon"] = "fa6s.folder"

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
        self.settings_changed.emit(
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
        self.settings_changed.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Filter settings were deleted.",
                flow=SignalFlow.COMPONENT_INTERACTION,
            )
        )

    @staticmethod
    def sanitize_media_label(label: Any) -> str:
        text = str(label).strip()
        if not text:
            return ""
        text = re.sub(r"[\\/:*?\"<>|]", "_", text)
        text = re.sub(r"[^a-zA-Z0-9_.\-\s]", "_", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = text.strip(" ._-")
        return text

    def get_db_path(self, folder_config: dict[str, Any], label_override: str | None = None) -> str:
        label = self.sanitize_media_label(
            label_override if label_override is not None else folder_config.get("label", "media")
        )
        if not label:
            label = "media"
        if label in {".", ".."}:
            label = "media"
        # Store DB path using POSIX separator to keep file naming consistent across platforms
        return f"db/{label}.db"

    def validate_media_configs(self, media_configs: list[dict[str, Any]]) -> list[str]:
        errors: list[str] = []
        seen_names: set[str] = set()

        for idx, config in enumerate(media_configs, start=1):
            label = str(config.get("label", "")).strip()
            path = str(config.get("path", "")).strip()
            safe_label = self.sanitize_media_label(label)

            if not label:
                errors.append(f"Media config #{idx} is missing a name.")
            elif not safe_label:
                errors.append(f"Media config #{idx} has an invalid name: '{label}'")

            if not path:
                errors.append(f"Media config '{label or f'#{idx}'}' is missing a folder path.")
            elif not Path(path).is_dir():
                errors.append(f"Media config '{label or f'#{idx}'}' path does not exist: {path}")

            if safe_label:
                normalized_name = safe_label.casefold()
                if normalized_name in seen_names:
                    errors.append(f"Media names must be unique. '{safe_label}' is used more than once.")
                seen_names.add(normalized_name)

        return errors

    def rename_db_for_media_config(self, media_config: dict[str, Any]) -> None:
        previous_label = str(media_config.get("_previous_label", "")).strip()
        current_label = str(media_config.get("label", "")).strip()
        if not previous_label or previous_label == current_label:
            return

        old_db = Path(self.get_db_path({"label": previous_label}, previous_label))
        new_db = Path(self.get_db_path({"label": current_label}, current_label))

        if old_db.resolve() == new_db.resolve():
            media_config["_previous_label"] = current_label
            return

        if new_db.exists() and not old_db.exists():
            raise ValueError(
                f"The database file '{new_db.name}' already exists. "
                "Please choose a unique media name."
            )

        if old_db.exists():
            try:
                old_db.replace(new_db)
            except OSError as exc:
                raise OSError(
                    f"Unable to rename database file from '{old_db.name}' to '{new_db.name}'. "
                    f"Original media name kept. Details: {exc}"
                ) from exc

        media_config["_previous_label"] = current_label

    def sync_db_file_names(self, media_configs: list[dict[str, Any]]) -> None:
        for config in media_configs:
            if not isinstance(config, dict):
                continue
            self.rename_db_for_media_config(config)

    def db_enabled(self) -> bool:
        # Check if the setting is 'Yes' (True)
        if not self._db_enabled:
            return False

        # Check if at least one DB exists
        for media_config in self.media_configs:
            db_path = self.get_db_path(media_config)
            if Path(db_path).exists():
                return True
        return False


    def save_settings(self) -> None:
        """Save all tabs' settings"""
        self.save_app()
        self.save_ui()
        self.save_media()
        self.save_filters()
