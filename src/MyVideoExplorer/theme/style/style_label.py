from MyVideoExplorer.theme.models import ThemeConfig


class StyleLabel:
    @staticmethod
    def get_label_qss(c: ThemeConfig, variant: str = "default") -> str:
        color = c.color_text_primary
        weight = "normal"
        padding = "0px"
        extra_label = ""
        extra_qss = ""

        # Only set font-size in QSS if it's a specific variant that deviates from base.
        # Otherwise, let setFont() on the widget handle it to avoid conflicts.
        font_size_qss = f"font-size: {c.font_size_base}px;"

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
            padding = "0px"
            extra_label = f"""
                margin: 0 0 3px 0;
                border-radius: 7px;
                border-bottom: 2px solid {c.color_border_default};
            """
        elif variant == "app_loading":
            font_size_qss = f"font-size: {c.font_size_base + 10}px;"
            weight = "700"
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
        font_qss = f"""
            font-family: {c.font_family_default};
            {font_size_qss}
        """

        return f"""
             QLabel {{
                 color: {color};
                 {font_size_qss}
                 font-weight: {weight};
                 padding: {padding};
                 {font_qss}
                 {extra_label}
             }}
             {extra_qss}
         """
