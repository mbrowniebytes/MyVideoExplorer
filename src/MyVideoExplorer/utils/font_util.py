from pathlib import Path

from PySide6.QtGui import QFontDatabase

from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.log_util import LogUtil


class FontUtil:
    def __init__(self, log_util: LogUtil, file_util: FileUtil) -> None:
        self.log_util = log_util
        self.file_util = file_util

        self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def load_custom_fonts(self):
        """Loads all .ttf and .otf fonts from the specified directory."""
        path_to_fonts = self.file_util.get_resource_path("asset/fonts")
        fonts_dir = Path(path_to_fonts)
        if not fonts_dir.exists():
            self.log_util.error(f"Font directory not found: {fonts_dir}")
            return

        self.log_util.debug(f"Loading fonts from: {fonts_dir}")

        loaded_fonts = []
        for font_file in fonts_dir.glob("*.ttf"):
            if QFontDatabase.addApplicationFont(str(font_file)) != -1:
                loaded_fonts.append(font_file.name)
        # for font_file in fonts_dir.glob("*.otf"):
        #     if QFontDatabase.addApplicationFont(str(font_file)) != -1:
        #         loaded_fonts.append(font_file.name)

        if loaded_fonts:
            self.log_util.debug(f"Using font: {loaded_fonts[0]}")
        else:
            self.log_util.debug(f"No custom fonts found in {fonts_dir}")
