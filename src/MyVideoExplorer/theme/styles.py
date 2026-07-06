from MyVideoExplorer.theme.theme import ThemeConfig


class StyleFactory:
    """Generates QSS strings based on a ThemeConfig."""

    @staticmethod
    def get_app_qss(c: ThemeConfig, include_font: bool = True) -> str:
        font_qss = ""
        if include_font:
            font_qss = f"""
                font-family: {c.font_family_default};
                font-size: {c.font_size_base}px;
            """
        return f"""
            QWidget {{
                background: {c.color_background_main};
                color: {c.color_text_primary};
                {font_qss}
            }}
            QMainWindow {{
                background: {c.color_background_main};
                {font_qss}
            }}
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {c.color_border_default};
                border-radius: {c.size_border_radius_standard}px;
                margin-top: 1.5ex;
                padding: 10px;
                {font_qss}
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                {font_qss}
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
                border: 2px solid {c.color_border_default};
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c.color_scrollbar_handle_hover};
            }}
            QToolTip {{
                background-color: {c.color_surface_primary};
                color: {c.color_text_primary};
                border: 1px solid {c.color_border_default};
                font-size: {c.font_size_base - 2}px;
                padding: 5px;
                {font_qss}
            }}
            QTextEdit, QLabel, QPlainTextEdit, QGroupBox, QCheckBox, QTableView {{
                {font_qss}
            }}
        """

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
    def get_checkbox_style(c: ThemeConfig) -> str:
        return f"""
            QCheckBox::indicator {{
                subcontrol-position: left top;
                background-color: #666666;
                border-radius: 2px;
                border-style: solid;
                border-width: 2px;
                border-color: #AAAAAA #AAAAAA #999999 #999999;
            }}
            QCheckBox::indicator:checked {{
                background-color: {c.color_interaction_selected};
            }}
         """
        # Source - https://stackoverflow.com/a/71518367
        return """
            QCheckBox::indicator {
                width: 30px;
                height: 30px;
                background-color: gray;
                border-radius: 15px;
                border-style: solid;
                border-width: 1px;
                border-color: white white black black;
            }
            QCheckBox::indicator:checked {
                background-color: qradialgradient(spread:pad,
                    cx:0.5,
                    cy:0.5,
                    radius:0.9,
                    fx:0.5,
                    fy:0.5,
                    stop:0 rgba(0, 255, 0, 255),
                    stop:1 rgba(0, 64, 0, 255)
                );
            }
            QCheckBox:checked, QCheckBox::indicator:checked {
                border-color: black black white white;
            }
            QCheckBox:checked {
                background-color: qradialgradient(spread:pad,
                    cx:0.739,
                    cy:0.278364,
                    radius:0.378,
                    fx:0.997289,
                    fy:0.00289117,
                    stop:0 rgba(255, 255, 255, 255),
                    stop:1 rgba(160, 160, 160, 255)
                );
            }
         """

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
        color = c.color_text_primary
        weight = "normal"
        padding = "0px"
        extra_label = ""
        extra_qss = ""

        # Only set font-size in QSS if it's a specific variant that deviates from base.
        # Otherwise, let setFont() on the widget handle it to avoid conflicts.
        font_size_qss = ""

        if variant == "small":
            font_size_qss = f"font-size: {c.font_size_base - 3}px;"
        elif variant == "secondary":
            color = c.color_text_secondary
        elif variant == "field_value":
            color = c.color_text_field_value
            extra_label = f"""
                border-radius: 6px;
                border-bottom: 1px solid {c.color_section_divider};
            """
        elif variant == "title":
            font_size_qss = f"font-size: {c.font_size_base + 10}px;"
            weight = "700"
            padding = "2px 0px 2px 0px"
            extra_label = f"""
                border-radius: 8px;
                border-bottom: 2px solid {c.color_border_default};
            """
        elif variant == "help_icon":
            font_size_qss = f"font-size: {c.font_size_base - 2}px;"
            extra_label = f"""
                border-radius: 6px;
                border: 2px solid {c.color_border_icon};
            """
            extra_qss = f"""
                QLabel:hover {{
                    border: 2px solid {c.color_border_highlight};
                }}
            """

        return f"""
             QLabel {{
                 color: {color};
                 {font_size_qss}
                 font-weight: {weight};
                 padding: {padding};
                 {extra_label}
             }}
             QToolTip {{
                 background-color: {c.color_surface_primary};
                 color: {c.color_text_primary};
                 border: 2px solid {c.color_border_highlight};
                 font-size: {c.font_size_base - 2}px;
                 padding: 5px;
             }}
             {extra_qss}
         """

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
                 background: {c.color_background_main};
                 border: none;
                 color: transparent;
             }}
        """
