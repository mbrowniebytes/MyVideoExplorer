from MyVideoExplorer.theme.models import ThemeConfig

class StyleCheckbox:
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
