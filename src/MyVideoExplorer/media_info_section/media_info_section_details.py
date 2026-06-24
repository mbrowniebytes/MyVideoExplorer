from PySide6.QtWidgets import QHeaderView, QSizePolicy, QVBoxLayout, QWidget

from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.base_widget import BaseWidget
from MyVideoExplorer.widgets.label_value_widget import LabelValueWidget
from MyVideoExplorer.widgets.simple_table_widget import SimpleTableWidget


class MediaInfoDetailsSection(BaseWidget):
    VIDEO_TABLE_COLUMN_KEYS = [
        "resolution",
        "codec",
        "bitrate",
        "runtime",
        "language",
        "aspect",
        "width",
        "height",
        "format",
    ]
    VIDEO_TABLE_COLUMN_HEADERS = [
        "Resolution",
        "Codec",
        "Bitrate",
        "Runtime",
        "Language",
        "Aspect",
        "Width",
        "Height",
        "Format",
    ]
    VIDEO_TABLE_COLUMN_RESIZE_MODES = [
        QHeaderView.ResizeMode.ResizeToContents,
    ] * len(VIDEO_TABLE_COLUMN_KEYS)

    AUDIO_TABLE_COLUMN_KEYS = ["channels", "codec", "bitrate", "language"]
    AUDIO_TABLE_COLUMN_HEADERS = ["Channels", "Codec", "Bitrate", "Language"]
    AUDIO_TABLE_COLUMN_RESIZE_MODES = [
        QHeaderView.ResizeMode.ResizeToContents,
        QHeaderView.ResizeMode.ResizeToContents,
        QHeaderView.ResizeMode.ResizeToContents,
        QHeaderView.ResizeMode.Stretch,
    ]

    SUBTITLE_TABLE_COLUMN_KEYS = ["language"]
    SUBTITLE_TABLE_COLUMN_HEADERS = ["Language"]
    SUBTITLE_TABLE_COLUMN_RESIZE_MODES = [QHeaderView.ResizeMode.Stretch]

    def __init__(
        self, log_util: LogUtil | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(log_util or LogUtil(), parent)

        self._current_identifier_items: list[dict] = []
        self._current_video_items: list[dict] = []
        self._current_audio_items: list[dict] = []
        self._current_subtitle_items: list[dict] = []

        self.details_section_layout = QVBoxLayout(self)

        self._configure_section_frame()
        self._configure_section_layout()

    def _configure_section_frame(self) -> None:
        self.setStyleSheet(APP_THEME.bottom_border_qss())
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def _configure_section_layout(self) -> None:
        self.details_section_layout.setContentsMargins(0, 0, 0, 0)
        self.details_section_layout.setSpacing(0)

    def _clear_details_section_layout(self) -> None:
        self._clear_layout_items(self.details_section_layout)

    def _clear_layout_items(self, target_layout: QVBoxLayout) -> None:
        while target_layout.count():
            layout_item = target_layout.takeAt(0)
            child_widget = layout_item.widget()
            child_layout = layout_item.layout()

            if child_widget is not None:
                child_widget.deleteLater()
            elif child_layout is not None:
                self._clear_layout_items(child_layout)

    def build_ids(self, identifier_items: list[dict]) -> None:
        self.setObjectName("section_ids")

        if self._current_identifier_items == identifier_items:
            return

        self._current_identifier_items = identifier_items
        identifiers_html = self._build_identifiers_html(identifier_items)

        existing_identifier_widget = self._find_existing_label_value_widget()

        if existing_identifier_widget is not None:
            existing_identifier_widget.set_value(identifiers_html)
            return

        self._clear_details_section_layout()
        self.details_section_layout.addWidget(
            LabelValueWidget(
                "IDs:", identifiers_html, log_util=self.log_util, parent=self
            )
        )

    def build_videos(self, video_items: list[dict]) -> None:
        self.setObjectName("section_videos")

        if self._current_video_items == video_items:
            return

        self._current_video_items = video_items
        self._build_or_update_table_section(
            section_title="Videos",
            table_rows=video_items,
            table_column_keys=self.VIDEO_TABLE_COLUMN_KEYS,
            table_column_headers=self.VIDEO_TABLE_COLUMN_HEADERS,
            table_column_resize_modes=self.VIDEO_TABLE_COLUMN_RESIZE_MODES,
        )

    def build_audios(self, audio_items: list[dict]) -> None:
        self.setObjectName("section_audios")

        if self._current_audio_items == audio_items:
            return

        self._current_audio_items = audio_items
        self._build_or_update_table_section(
            section_title="Audios",
            table_rows=audio_items,
            table_column_keys=self.AUDIO_TABLE_COLUMN_KEYS,
            table_column_headers=self.AUDIO_TABLE_COLUMN_HEADERS,
            table_column_resize_modes=self.AUDIO_TABLE_COLUMN_RESIZE_MODES,
        )

    def build_subtitles(self, subtitle_items: list[dict]) -> None:
        self.setObjectName("section_subtitles")

        if self._current_subtitle_items == subtitle_items:
            return

        self._current_subtitle_items = subtitle_items
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._build_or_update_table_section(
            section_title="Subtitles",
            table_rows=subtitle_items,
            table_column_keys=self.SUBTITLE_TABLE_COLUMN_KEYS,
            table_column_headers=self.SUBTITLE_TABLE_COLUMN_HEADERS,
            table_column_resize_modes=self.SUBTITLE_TABLE_COLUMN_RESIZE_MODES,
        )

    def _build_or_update_table_section(
        self,
        section_title: str,
        table_rows: list[dict],
        table_column_keys: list[str],
        table_column_headers: list[str],
        table_column_resize_modes: list[QHeaderView.ResizeMode],
    ) -> None:
        existing_table_widget = self._find_existing_table_widget()

        if existing_table_widget is not None:
            existing_table_widget.update_rows(rows=table_rows)
            return

        self._clear_details_section_layout()
        self.details_section_layout.addWidget(
            LabelValueWidget(section_title, log_util=self.log_util, parent=self)
        )
        table = SimpleTableWidget(
            rows=table_rows,
            cols=table_column_keys,
            headers=table_column_headers,
            resize_modes=table_column_resize_modes,
            parent=self,
        )
        self.details_section_layout.addWidget(table)

    def _find_existing_label_value_widget(self) -> LabelValueWidget | None:
        for layout_index in range(self.details_section_layout.count()):
            layout_widget = self.details_section_layout.itemAt(layout_index).widget()

            if isinstance(layout_widget, LabelValueWidget):
                return layout_widget

        return None

    def _find_existing_table_widget(self) -> SimpleTableWidget | None:
        for layout_index in range(self.details_section_layout.count()):
            layout_widget = self.details_section_layout.itemAt(layout_index).widget()

            if isinstance(layout_widget, SimpleTableWidget):
                return layout_widget

        return None

    def _build_identifiers_html(self, identifier_items: list[dict]) -> str:
        identifier_html_fragments: list[str] = []

        for media_identifier_item in identifier_items:
            identifier_type = media_identifier_item.get("type", "")
            identifier_value = media_identifier_item.get("id", "")

            if identifier_type == "imdbid":
                identifier_html_fragments.append(
                    f'<a href="https://www.imdb.com/title/{identifier_value}/">'
                    f"{identifier_type}: {identifier_value}</a>"
                )
            elif identifier_type == "tmdbid":
                identifier_html_fragments.append(
                    f'<a href="https://www.themoviedb.org/movie/{identifier_value}/">'
                    f"{identifier_type}: {identifier_value}</a>"
                )
            else:
                identifier_html_fragments.append(
                    f"<i>{identifier_type}: {identifier_value}</i>"
                )

        return ", ".join(identifier_html_fragments)

    def apply_theme(self) -> None:
        super().apply_theme()
        self.setStyleSheet(APP_THEME.table_qss())
        self.setStyleSheet(APP_THEME.bottom_border_qss())
