from PySide6.QtWidgets import QTabBar
from PySide6.QtCore import Qt, QSize


class RightAlignedTabBar(QTabBar):
    """
    A custom QTabBar implementation designed to support right-aligned tab layouts.
    This component is intended to be used within a QTabWidget or a custom layout
    where tab positioning needs to be controlled.
    """
    
    def __init__(self, parent=None, spacer_index: int | None = None) -> None:
        super().__init__(parent)
        self.setExpanding(True)
        self._spacer_index = spacer_index

    def tabSizeHint(self, index: int) -> QSize:
        """
        Returns the size hint for the tab at the given index.

        Args:
            index: The index of the tab.

         Returns:
             QSize: The recommended size for the tab.
         """

        size = super().tabSizeHint(index)

        # Determine spacer index: use provided one or default to count - 2
        spacer_idx = self._spacer_index
        if spacer_idx is None:
            spacer_idx = self.count() - 2

        # Handle negative index (e.g. -1 for last tab, -2 for second to last)
        if spacer_idx < 0:
            spacer_idx = self.count() + spacer_idx

        if index == spacer_idx:
            # Calculate remaining space
            total_width = self.parent().width() if self.parent() else self.width()
            tabs_width = 0
            for i in range(self.count()):
                if i != index:
                    tabs_width += super().tabSizeHint(i).width()

            # If there's extra space, make the spacer expand
            if total_width > tabs_width:
                return size.expandedTo(
                    size.scaled(
                        total_width - tabs_width,
                        size.height(),
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                    )
                )
        return size
