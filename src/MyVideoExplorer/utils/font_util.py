from pathlib import Path

from PySide6.QtGui import QFontDatabase

from MyVideoExplorer.utils.log_util import LogUtil


class FontUtil:
    def __init__(self, log_util: LogUtil) -> None:
        self.log_util = log_util

        self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def load_custom_fonts(self, fonts_dir: Path):
        """Loads all .ttf and .otf fonts from the specified directory."""
        if not fonts_dir.exists():
            print(f"Font directory not found: {fonts_dir}")
            return

        loaded_fonts = 0
        for font_file in fonts_dir.glob("*.ttf"):
            if QFontDatabase.addApplicationFont(str(font_file)) != -1:
                loaded_fonts += 1
        # for font_file in fonts_dir.glob("*.otf"):
        #     if QFontDatabase.addApplicationFont(str(font_file)) != -1:
        #         loaded_fonts += 1

        print(f"Loaded {loaded_fonts} custom fonts from {fonts_dir}")
