from MyVideoExplorer.theme.models import ThemeConfig


class StyleTable:
    @staticmethod
    def get_table_qss(c: ThemeConfig) -> str:
        font_qss = f"""
            font-family: {c.font_family_default};
            font-size: {c.font_size_base}px;
        """
        return f"""
             QTableView, QTableWidget {{
                 background: {c.color_background_main};
                 color: {c.color_text_primary};
                 gridline-color: {c.color_border_default};
                 border: 1px solid {c.color_border_default};
                 selection-background-color: {c.color_interaction_selected};
                 selection-color: {c.color_interaction_selected_text};
                 {font_qss}
             }}
             QHeaderView::section {{
                 background: {c.color_surface_primary};
                 color: {c.color_text_primary};
                 padding: 0px;
                 border: 0;
                 {font_qss}
             }}
         """
