from MyVideoExplorer.theme.models import ThemeConfig

class StyleList:
    @staticmethod
    def get_list_qss(c: ThemeConfig) -> str:
        font_qss = f"""
            font-family: {c.font_family_default};
            font-size: {c.font_size_base}px;
        """
        return f"""
            QListWidget {{
                background: {c.color_background_main};
                color: {c.color_text_primary};
                border: 1px solid {c.color_border_default};
                border-radius: {c.size_border_radius_standard}px;
                outline: 0;
                {font_qss}
            }}
            QListWidget::item {{
                padding: {c.padding_list_item_vertical}px {c.padding_list_item_horizontal}px;
                margin: {c.margin_list_item_vertical}px {c.margin_list_item_horizontal}px;
                border-radius: {max(0, c.size_border_radius_standard - 2)}px;
            }}
            QListWidget::item:alternate {{
                background: {c.color_surface_alternate};
            }}
            QListWidget::item:selected {{
                background: {c.color_interaction_selected};
                color: {c.color_interaction_selected_text};
            }}
            QListWidget::item:hover {{
                background: {c.color_interaction_selected};
            }}
            QListWidget QScrollBar:horizontal {{
                border: none;
                background: {c.color_scrollbar_background};
                margin: 1px;
            }}
            QListWidget QScrollBar::handle:horizontal {{
                background: {c.color_scrollbar_handle};
                border-radius: 7px;
                min-height: 30px;
                border: 2px solid {c.color_border_default};
                margin: 2px;
            }}
            QListWidget QScrollBar::handle:horizontal:hover {{
                background: {c.color_scrollbar_handle_hover};
            }}
        """
