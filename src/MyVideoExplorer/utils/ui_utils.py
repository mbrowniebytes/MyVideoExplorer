from __future__ import annotations
from PySide6.QtWidgets import QLayout, QVBoxLayout, QWidget

class UIUtils:
    def apply_compact_layout(self, widget: QWidget, layout_type: type[QLayout] = QVBoxLayout) -> QLayout:
        """Creates and sets a layout with 0 margins and 0 spacing."""
        if widget.layout() is not None:
            raise RuntimeError(
                "Widget already has a layout. Clear it first or use clear_self_layout()."
            )

        layout = layout_type(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        widget.setLayout(layout)
        return layout

    def clear_layout(self, layout: QLayout | None) -> None:
        """Utility to safely clear all widgets and sub-layouts from a layout."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def clear_self_layout(self, widget: QWidget) -> None:
        """Convenience method to clear the widget's own layout."""
        self.clear_layout(widget.layout())
