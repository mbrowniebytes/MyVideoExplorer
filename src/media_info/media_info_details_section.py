from PySide6.QtWidgets import QFrame, QVBoxLayout, QHeaderView, QSizePolicy
from src.theme.theme import APP_THEME
from src.widgets.simple_table_widget import SimpleTableWidget
from src.widgets.label_value_widget import LabelValueWidget


class MediaInfoDetailsSection(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(APP_THEME.bottom_border_qss())
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def _clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def _clear_sub_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def build_ids(self, ids: list[dict]) -> None:
        self.setObjectName("section_ids")
        if hasattr(self, "_current_ids") and self._current_ids == ids:
            return
        self._current_ids = ids

        ids_html = self._build_ids_html(ids)

        # Try to find existing LabelValueWidget
        existing_widget = None
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if isinstance(w, LabelValueWidget):
                existing_widget = w
                break

        if existing_widget:
            existing_widget.set_value(ids_html)
        else:
            self._clear_layout()
            self.layout.addWidget(LabelValueWidget("IDs:", ids_html))

    def build_videos(self, videos: list[dict]) -> None:
        self.setObjectName("section_videos")
        if hasattr(self, "_current_videos") and self._current_videos == videos:
            return
        self._current_videos = videos

        # Try to find existing Table
        existing_table = None
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if isinstance(w, SimpleTableWidget):
                existing_table = w
                break

        if existing_table:
            existing_table.update_rows(rows=videos)
        else:
            self._clear_layout()
            self.layout.addWidget(LabelValueWidget("Videos"))
            self.layout.addWidget(
                SimpleTableWidget(
                    rows=videos,
                    cols=[
                        "resolution",
                        "codec",
                        "bitrate",
                        "runtime",
                        "language",
                        "aspect",
                        "width",
                        "height",
                        "format",
                    ],
                    headers=[
                        "Resolution",
                        "Codec",
                        "Bitrate",
                        "Runtime",
                        "Language",
                        "Aspect",
                        "Width",
                        "Height",
                        "Format",
                    ],
                    resize_modes=[QHeaderView.ResizeMode.ResizeToContents] * 9,
                )
            )

    def build_audios(self, audios: list[dict]) -> None:
        self.setObjectName("section_audios")
        if hasattr(self, "_current_audios") and self._current_audios == audios:
            return
        self._current_audios = audios

        # Try to find existing Table
        existing_table = None
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if isinstance(w, SimpleTableWidget):
                existing_table = w
                break

        if existing_table:
            existing_table.update_rows(rows=audios)
        else:
            self._clear_layout()
            self.layout.addWidget(LabelValueWidget("Audios"))
            self.layout.addWidget(
                SimpleTableWidget(
                    rows=audios,
                    cols=["channels", "codec", "bitrate", "language"],
                    headers=["Channels", "Codec", "Bitrate", "Language"],
                    resize_modes=[
                        QHeaderView.ResizeMode.ResizeToContents,
                        QHeaderView.ResizeMode.ResizeToContents,
                        QHeaderView.ResizeMode.ResizeToContents,
                        QHeaderView.ResizeMode.Stretch,
                    ],
                )
            )

    def build_subtitles(self, subtitles: list[dict]) -> None:
        self.setObjectName("section_subtitles")
        if hasattr(self, "_current_subtitles") and self._current_subtitles == subtitles:
            return
        self._current_subtitles = subtitles

        # Try to find existing Table
        existing_table = None
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if isinstance(w, SimpleTableWidget):
                existing_table = w
                break

        if existing_table:
            existing_table.update_rows(rows=subtitles)
        else:
            self._clear_layout()
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.layout.addWidget(LabelValueWidget("Subtitles"))
            self.layout.addWidget(
                SimpleTableWidget(
                    rows=subtitles,
                    cols=["language"],
                    headers=["Language"],
                    resize_modes=[QHeaderView.ResizeMode.Stretch],
                )
            )

    def _build_ids_html(self, ids: list[dict]) -> str:
        ids_text = ""
        for item in ids:
            id_type = item.get("type", "")
            id_val = item.get("id", "")
            if id_type == "imdbid":
                ids_text += f'<a href="https://www.imdb.com/title/{id_val}/">{id_type}: {id_val}</a>, '
            elif id_type == "tmdbid":
                ids_text += f'<a href="https://www.themoviedb.org/movie/{id_val}/">{id_type}: {id_val}</a>, '
            else:
                ids_text += f"<i>{id_type}: {id_val}</i>, "
        return ids_text.rstrip(", ")
