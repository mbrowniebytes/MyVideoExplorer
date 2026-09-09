from MyVideoExplorer.theme.models import ThemeConfig


class StyleCombo:
    @staticmethod
    def get_combo_qss(c: ThemeConfig) -> str:
        font_qss = f"""
            font-family: {c.font_family_default};
            font-size: {c.font_size_base}px;
        """
        return f"""
            QComboBox {{
                background: {c.color_surface_primary};
                color: {c.color_text_primary};
                border: 1px solid {c.color_border_default};
                border-radius: {c.size_border_radius_standard}px;
                padding: 2px 4px;
                {font_qss}
            }}
            QComboBox QAbstractItemView {{
                background: {c.color_surface_primary};
                selection-background-color: {c.color_interaction_selected};
                border: 1px solid {c.color_border_default};
            }}
        """
