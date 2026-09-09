from __future__ import annotations
from MyVideoExplorer.theme.models import ThemeConfig
from MyVideoExplorer.theme.style.style_app import StyleApp
from MyVideoExplorer.theme.style.style_button import StyleButton
from MyVideoExplorer.theme.style.style_label import StyleLabel
from MyVideoExplorer.theme.style.style_layout import StyleLayout
from MyVideoExplorer.theme.style.style_list import StyleList
from MyVideoExplorer.theme.style.style_progress_bar import StyleProgressBar
from MyVideoExplorer.theme.style.style_tab import StyleTab
from MyVideoExplorer.theme.style.style_table import StyleTable
from MyVideoExplorer.theme.manager import ThemeManager


class Theme(ThemeManager):
    """
    Main theme entry point.
    """

    def __init__(self, config: ThemeConfig | None = None):
        super().__init__(config or ThemeConfig())

    @property
    def font_size(self) -> int:
        return self.config.font_size_base

    @font_size.setter
    def font_size(self, value: int):
        self.config.font_size_base = value

    @property
    def font_family(self) -> str:
        return self.config.font_family_default

    @font_family.setter
    def font_family(self, value: str):
        self.config.font_family_default = value

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
        return StyleButton.get_button_qss(self.config)

    def button_highlight_qss(self) -> str:
        return StyleButton.get_button_highlight_qss(self.config)

    def label_qss(self, variant: str | None = None) -> str:
        return StyleLabel.get_label_qss(self.config, variant=variant or "default")

    def help_icon_label_qss(self) -> str:
        return StyleLabel.get_label_qss(self.config, variant="help_icon")

    def secondary_label_qss(self) -> str:
        return StyleLabel.get_label_qss(self.config, variant="secondary")

    def title_label_qss(self) -> str:
        return StyleLabel.get_label_qss(self.config, variant="title")

    def loading_label_qss(self) -> str:
        return StyleLabel.get_label_qss(self.config, variant="app_loading")

    def field_value_qss(self) -> str:
        return StyleLabel.get_label_qss(self.config, variant="field_value")

    def list_qss(self) -> str:
        return StyleList.get_list_qss(self.config)

    def table_qss(self) -> str:
        return StyleTable.get_table_qss(self.config)

    def bottom_border_qss(self) -> str:
        return StyleLayout.get_bottom_border_qss(self.config)

    def separator_line_qss(self) -> str:
        return StyleLayout.get_separator_line_qss(self.config)

    def settings_media_folder_browser_section_qss(self) -> str:
        return StyleLayout.get_settings_media_folder_browser_section_qss(self.config)

    def splitter_qss(self) -> str:
        return StyleLayout.get_splitter_qss(self.config)

    def tabs_qss(self) -> str:
        return StyleTab.get_tabs_qss(self.config)

    def media_section_container_qss(self) -> str:
        return StyleLayout.get_media_section_container_qss(self.config)

    def progress_bar_qss(self, active: bool = True) -> str:
        return StyleProgressBar.get_progress_bar_qss(self.config, active=active)

    def small_button_qss(self) -> str:
        return StyleButton.get_small_button_qss(self.config)

    def container_qss(self) -> str:
        return StyleApp.get_app_qss(self.config)

    def app_qss(self) -> str:
        return StyleApp.get_app_qss(self.config)

    def icon(self, name: str, **kwargs):
        return self.get_icon(name, **kwargs)


APP_THEME = Theme()
