from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import Signal
from src.app.app_signals_model import SignalPayload, SignalFlow

class GenreComboWidget(QComboBox):
    sig_genre_changed = Signal(object)

    def __init__(self, genres: list[str], parent=None):
        super().__init__(parent)
        self.genres = genres
        self.addItem("-none-")
        for genre in self.genres:
            self.addItem(genre)

        self.currentTextChanged.connect(self._on_genre_changed)

    def _on_genre_changed(self, genre: str):
        payload = SignalPayload(
            data=genre,
            sender=self.__class__.__name__,
            name="Genre Changed",
            description="Emitted when the genre changes in GenreComboWidget.",
            flow=SignalFlow.USER_INPUT,
        )
        self.sig_genre_changed.emit(payload)
