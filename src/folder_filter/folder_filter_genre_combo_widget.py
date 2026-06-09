from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import Signal

class GenreComboWidget(QComboBox):
    sig_genre_changed = Signal(str)

    def __init__(self, genres: list[str], parent=None):
        super().__init__(parent)
        self.genres = genres
        self.addItem("-none-")
        for genre in self.genres:
            self.addItem(genre)

        self.currentTextChanged.connect(self.sig_genre_changed.emit)
