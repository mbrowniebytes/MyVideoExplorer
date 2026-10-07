from MyVideoExplorer.theme.models import ThemeConfig


class StyleButton:
    @staticmethod
    def get_button_qss(c: ThemeConfig) -> str:
        return f"""
            QAbstractButton {{
                color: {c.color_text_primary};
                border: 2px solid {c.color_border_default};
                border-radius: {c.size_border_radius_standard}px;
                padding: {c.padding_button_standard_v}px {c.padding_button_standard_h}px;
                background: {c.color_surface_primary};
                text-align: center;
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
    def get_toggle_button_qss(c: ThemeConfig, widget_name: str) -> str:
        return f"""
            QAbstractButton#{widget_name},
            QAbstractButton#{widget_name}:hover,
            QAbstractButton#{widget_name}:pressed,
            QAbstractButton#{widget_name}:checked,
            QAbstractButton#{widget_name}:focus,
            QAbstractButton#{widget_name}:disabled,
            QToolButton#{widget_name},
            QToolButton#{widget_name}:hover,
            QToolButton#{widget_name}:pressed,
            QToolButton#{widget_name}:checked,
            QToolButton#{widget_name}:focus,
            QToolButton#{widget_name}:disabled {{
                border: none;
                outline: none;
                font-weight: normal;
            }}
            QAbstractButton#{widget_name},
            QToolButton#{widget_name} {{
                color: {c.color_text_primary};
                background: transparent;
                padding: 0 4px;
                font-size: 12px;
                font-weight: normal;
            }}
            QToolButton#{widget_name}:hover {{
                color: {c.color_text_primary};
                background: {c.color_interaction_hover};
            }}
            QToolButton#{widget_name}:checked {{
                color: {c.color_text_primary};
                background: transparent;
                padding: 0 4px;
                font-size: 12px;
                border: none;
            }}
            QToolButton#{widget_name}:checked:hover {{
                color: {c.color_text_primary};
                background: {c.color_interaction_hover};
            }}
        """

    @staticmethod
    def get_button_highlight_qss(c: ThemeConfig) -> str:
        return f"""
             QAbstractButton {{
                 border: 4px solid {c.color_border_highlight};
             }}
         """
