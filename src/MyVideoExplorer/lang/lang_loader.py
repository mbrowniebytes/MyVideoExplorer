from MyVideoExplorer.lang.lang_en import LangEn


class LangLoader:
    @staticmethod
    def get_lang(lang_code: str = "en"):
        if lang_code == "en":
            return LangEn()
        return LangEn()  # Default to English
