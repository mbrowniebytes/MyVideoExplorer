from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy
from src.theme.theme import APP_THEME
from src.widgets.base_widget import BaseWidget


class LabelValueWidget(BaseWidget):
    """
    A reusable widget for displaying a label and its corresponding value.
    Supports horizontal and vertical orientations and optional links.
    """

    def __init__(
        self,
        name: str,
        value: str | int | float | None = None,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        is_link: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.name = name
        self.value = value
        self.orientation = orientation
        self.is_link = is_link

        layout_type = (
            QHBoxLayout if orientation == Qt.Orientation.Horizontal else QVBoxLayout
        )
        self.layout = self.set_compact_layout(layout_type)
        self.layout.setSpacing(8 if orientation == Qt.Orientation.Horizontal else 4)

        self.label_name = QLabel(name or "")
        self.label_name.setWordWrap(False)
        self.label_name.setStyleSheet(APP_THEME.secondary_label_qss())
        self.label_name.setVisible(bool(name))

        self.label_value = QLabel()
        self.label_value.setWordWrap(True)
        self.label_value.setStyleSheet(APP_THEME.field_value_qss())

        if is_link:
            self.label_value.setTextFormat(Qt.TextFormat.RichText)
            self.label_value.setOpenExternalLinks(True)

        self.set_value(value)

        if orientation == Qt.Orientation.Horizontal:
            self.label_name.setSizePolicy(
                QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
            )
            self.label_value.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
        else:
            self.label_name.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            self.label_value.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            self.label_name.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.label_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.layout.addWidget(self.label_name)
        self.layout.addWidget(self.label_value)

    def set_value(self, value: str | int | float | None) -> None:
        """Updates the value displayed by the widget."""
        self.value = value
        self._update_display_value(value)

    def _update_display_value(self, value: str | int | float | None) -> None:
        """Internal method to handle label text formatting."""
        text = str(value) if value is not None else ""
        self.label_value.setText(text)
