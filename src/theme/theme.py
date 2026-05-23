from __future__ import annotations
from src.theme.models import ThemeConfig
from src.theme.styles import StyleFactory
from src.theme.manager import ThemeManager

class Theme(ThemeManager):
    """
    Main theme entry point.
    Maintains backward compatibility with original class name.
    """
    def __init__(self, config: ThemeConfig | None = None):
        super().__init__(config or ThemeConfig())

    # --- Backward Compatibility Properties ---
    # These allow existing code to access APP_THEME.font_size etc.
    # while mapping them to the new verbose config names.

    @property
    def font_size(self) -> int:
        return self.config.font_size_base

    @font_size.setter
    def font_size(self, value: int):
        self.config.font_size_base = value

    @property
    def font_family(self) -> str:
        return self.config.font_family_default

    @property
    def background_color(self) -> str:
        return self.config.color_background_main

    @property
    def surface_color(self) -> str:
        return self.config.color_surface_primary

    @property
    def text_color(self) -> str:
        return self.config.color_text_primary

    @property
    def border_color(self) -> str:
        return self.config.color_border_default

    @property
    def icon_size(self) -> int:
        return self.config.size_standard_icon

    # --- Backward Compatibility Methods ---

    def button_qss(self) -> str:
        return StyleFactory.get_button_qss(self.config)

    def button_highlight_qss(self) -> str:
        return StyleFactory.get_button_highlight_qss(self.config)

    def label_qss(self, variant: str | None = None) -> str:
        return StyleFactory.get_label_qss(self.config, variant=variant)

    def help_icon_label_qss(self) -> str:
        return StyleFactory.get_label_qss(self.config, variant="help_icon")

    def secondary_label_qss(self) -> str:
        return StyleFactory.get_label_qss(self.config, variant="secondary")

    def title_label_qss(self) -> str:
        return StyleFactory.get_label_qss(self.config, variant="title")

    def field_value_qss(self) -> str:
        return StyleFactory.get_label_qss(self.config, variant="field_value")

    def list_qss(self) -> str:
        return StyleFactory.get_list_qss(self.config)

    def table_qss(self) -> str:
        return StyleFactory.get_table_qss(self.config)

    def bottom_border_qss(self) -> str:
        return StyleFactory.get_bottom_border_qss(self.config)

    def splitter_qss(self) -> str:
        return StyleFactory.get_splitter_qss(self.config)

    def tabs_qss(self) -> str:
        return StyleFactory.get_tabs_qss(self.config)

    def small_button_qss(self) -> str:
        return StyleFactory.get_small_button_qss(self.config)

    def container_qss(self) -> str:
        return StyleFactory.get_app_qss(self.config)

    def app_qss(self) -> str:
        return StyleFactory.get_app_qss(self.config)

    def icon(self, name: str, **kwargs):
        return self.get_icon(name, **kwargs)

APP_THEME = Theme()
