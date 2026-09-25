from MyVideoExplorer.theme.models import ThemeConfig


class StyleTab:
    @staticmethod
    def get_tabs_qss(c: ThemeConfig) -> str:
        font_qss = f"""
            font-family: {c.font_family_default};
            font-size: {c.font_size_base}px;
        """
        return f"""
            QTabWidget::pane {{
                border: 1px solid {c.color_border_default};
                border-top: 0;
                background: {c.color_background_main};
                {font_qss}
            }}
            QTabBar::tab {{
                padding: 6px 16px;
                border-top-left-radius: {c.size_border_radius_standard}px;
                border-top-right-radius: {c.size_border_radius_standard}px;
                background: {c.color_surface_primary};
                color: {c.color_text_primary};
                margin-right: 2px;
                {font_qss}
            }}
            QTabBar::tab:selected {{
                background: {c.color_interaction_selected};
                color: {c.color_interaction_selected_text};
            }}
             QTabBar::tab:disabled {{
                 background: transparent;
                 border: none;
                 color: transparent;
                 padding: 0;
                 margin: 0;
             }}
        """
