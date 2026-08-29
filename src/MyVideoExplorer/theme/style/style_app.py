from MyVideoExplorer.theme.models import ThemeConfig

class StyleApp:
    @staticmethod
    def get_app_qss(c: ThemeConfig) -> str:
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
            QLabel {{
                {font_qss}
            }}
            QPlainTextEdit {{
                {font_qss}
            }}
            QGroupBox {{
                {font_qss}
            }}
            QCheckBox {{
                {font_qss}
            }}
            QTableView {{
                {font_qss}
            }}
        """
