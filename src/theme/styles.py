from src.theme.models import ThemeConfig

class StyleFactory:
    """Generates QSS strings based on a ThemeConfig."""

    @staticmethod
    def get_app_qss(c: ThemeConfig) -> str:
        return f"""
            QWidget {{
                background: {c.color_background_main};
                color: {c.color_text_primary};
                font-family: {c.font_family_default};
                font-size: {c.font_size_base}px;
            }}
            QMainWindow {{
                background: {c.color_background_main};
            }}
            QScrollBar:vertical {{
                border: none;
                background: {c.color_scrollbar_background};
                width: 14px;
            }}
            QScrollBar::handle:vertical {{
                background: {c.color_scrollbar_handle};
                min-height: 30px;
                border-radius: 7px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c.color_scrollbar_handle_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QToolTip {{
                background-color: {c.color_surface_primary};
                color: {c.color_text_primary};
                border: 1px solid {c.color_border_default};
                font-size: {c.font_size_base - 2}px;
                padding: 5px;
            }}
        """

    @staticmethod
    def get_list_qss(c: ThemeConfig) -> str:
        return f"""
            QListWidget {{
                background: {c.color_background_main};
                color: {c.color_text_primary};
                border: 1px solid {c.color_border_default};
                border-radius: {c.size_border_radius_standard}px;
                outline: 0;
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
                background: {c.color_interaction_hover};
            }}
        """

    @staticmethod
    def get_button_qss(c: ThemeConfig) -> str:
        return f"""
            QAbstractButton {{
                color: {c.color_text_primary};
                border: 2px solid {c.color_border_default};
                border-radius: {c.size_border_radius_standard}px;
                padding: {c.padding_button_standard_v}px {c.padding_button_standard_h}px;
                background: {c.color_surface_primary};
                text-align: left;
            }}
            QAbstractButton:hover {{
                background: {c.color_interaction_hover};
                border: 1px solid {c.color_interaction_selected};
            }}
            QAbstractButton:pressed {{
                background: {c.color_interaction_pressed};
            }}
            QAbstractButton:checked {{
                background: {c.color_interaction_selected};
                color: {c.color_interaction_selected_text};
                font-weight: bold;
            }}
            QAbstractButton:disabled {{
                background: {c.color_surface_disabled};
                border: 1px solid {c.color_surface_disabled};
            }}
            QPushButton {{ 
                text-align: center; 
            }}
        """

    @staticmethod
    def get_table_qss(c: ThemeConfig) -> str:
        return f"""
             QTableView, QTableWidget {{
                 background: {c.color_background_main};
                 color: {c.color_text_primary};
                 gridline-color: {c.color_border_default};
                 border: 1px solid {c.color_border_default};
                 selection-background-color: {c.color_interaction_selected};
                 selection-color: {c.color_interaction_selected_text};
             }}
             QHeaderView::section {{
                 background: {c.color_surface_primary};
                 color: {c.color_text_primary};
                 padding: 0px;
                 border: 0;
             }}
         """

    @staticmethod
    def get_small_button_qss(c: ThemeConfig) -> str:
        return f"""
             QAbstractButton {{
                 color: {c.color_text_primary};
                 border: 1px solid {c.color_border_default};
                 border-radius: {c.size_border_radius_standard}px;
                 padding: {c.padding_button_small_v}px {c.padding_button_small_h}px;
                 background: {c.color_surface_primary};
                 text-align: center;
             }}
             QAbstractButton:hover {{ background: {c.color_interaction_hover}; }}
             QAbstractButton:pressed {{ background: {c.color_interaction_pressed}; }}
             QAbstractButton:checked {{
                 background: {c.color_interaction_selected};
                 color: {c.color_interaction_selected_text};
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
    def get_button_highlight_qss(c: ThemeConfig) -> str:
        return f"""
             QAbstractButton {{
                 border: 4px solid {c.color_border_highlight};
             }}
         """

    @staticmethod
    def get_combo_qss(c: ThemeConfig) -> str:
        return f"""
            QComboBox {{
                background: {c.color_surface_primary};
                color: {c.color_text_primary};
                border: 1px solid {c.color_border_default};
                border-radius: {c.size_border_radius_standard}px;
                padding: 4px 8px;
                min-height: 32px;
            }}
            QComboBox QAbstractItemView {{
                background: {c.color_surface_primary};
                selection-background-color: {c.color_interaction_selected};
                border: 1px solid {c.color_border_default};
            }}
        """

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
    def get_label_qss(c: ThemeConfig, variant: str = "default") -> str:
        size = c.font_size_base
        color = c.color_text_primary
        weight = "normal"
        padding = "0px"
        extra = ""

        if variant == "small":
            size -= 3
        elif variant == "secondary":
            color = c.color_text_secondary
        elif variant == "field_value":
            color = c.color_text_field_value
            extra = f"""
                border-radius: 8px;
                border-bottom: 1px solid {c.color_section_divider};
            """
        elif variant == "title":
            size += 10
            weight = "700"
            padding = "4px 0px 12px 0px"
            extra = f"""
                border-radius: 8px;
                border-bottom: 2px solid {c.color_border_default};
            """
        elif variant == "help_icon":
            size -= 3
            extra = f"""
                border-radius: 6px;
                border: 2px solid {c.color_border_icon};
            """

        return f"""
             QLabel {{
                 color: {color};
                 font-family: {c.font_family_default};
                 font-size: {size}px;
                 font-weight: {weight};
                 padding: {padding};
                 {extra}
             }}
             QToolTip {{
                 background-color: {c.color_surface_primary};
                 color: {c.color_text_primary};
                 border: 1px solid {c.color_border_default};
                 font-size: {c.font_size_base - 2}px;
                 padding: 5px;
             }}
         """

    @staticmethod
    def get_tabs_qss(c: ThemeConfig) -> str:
        return f"""
            QTabWidget::pane {{
                border: 1px solid {c.color_border_default};
                border-top: 0;
                background: {c.color_background_main};
            }}
            QTabBar::tab {{
                padding: 6px 16px;
                border-top-left-radius: {c.size_border_radius_standard}px;
                border-top-right-radius: {c.size_border_radius_standard}px;
                background: {c.color_surface_primary};
                color: {c.color_text_primary};
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {c.color_interaction_selected};
                color: {c.color_interaction_selected_text};
            }}
             QTabBar::tab:disabled {{
                 background: {c.color_background_main};
                 border: none;
                 color: transparent;
             }}
        """
