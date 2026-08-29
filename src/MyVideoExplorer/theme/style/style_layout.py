from MyVideoExplorer.theme.models import ThemeConfig

class StyleLayout:
    @staticmethod
    def get_splitter_qss(c: ThemeConfig) -> str:
        return f"""
            QSplitter::handle {{
                background-color: {c.color_splitter_handle};
            }}
            QSplitter::handle:horizontal {{
                width: {c.size_splitter_handle_width}px;
            }}
            QSplitter::handle:vertical {{
                height: {c.size_splitter_handle_width + 1}px;
            }}
        """

    @staticmethod
    def get_media_section_container_qss(c: ThemeConfig) -> str:
        return f"""
            #media_section_container {{
                border-radius: 7px;
                background-color: {c.color_background_section};
                padding: 2px;
            }}
        """

    @staticmethod
    def get_bottom_border_qss(c: ThemeConfig) -> str:
        return f"""
             QFrame {{
                 border-bottom: 1px solid {c.color_section_divider};
             }}
        """

    @staticmethod
    def get_separator_line_qss(c: ThemeConfig) -> str:
        return f"""
            QFrame {{
                border: 1px solid {c.color_section_divider};
            }}
        """

    @staticmethod
    def get_settings_media_folder_browser_section_qss(c: ThemeConfig) -> str:
        return f"""
             SettingsMediaFolderBrowserSection {{
                 border-bottom: 4px inset {c.settings_media_folder_browser_section_divider};
                 border-radius: 7px;
                 padding: 2px 0 2px 0;
                 margin: 2px 0 6px 0;
             }}
        """
