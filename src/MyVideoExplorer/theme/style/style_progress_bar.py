from MyVideoExplorer.theme.models import ThemeConfig


class StyleProgressBar:
    @staticmethod
    def get_progress_bar_qss(c: ThemeConfig, active: bool = True) -> str:
        if active:
            return f"""
                QProgressBar {{
                    border: 1px solid {c.color_border_default};
                    background: {c.color_background_main};
                    border-radius: 7px;
                }}
                QProgressBar::chunk {{
                    background: {c.color_border_default};
                    border-radius: 3px;
                }}
            """
        else:
            return """
                QProgressBar {
                    border: none;
                    background: transparent;
                }
                QProgressBar::chunk {
                    background: transparent;
                }
            """
