from typing import cast

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QTabBar, QWidget


class RightAlignedTabBar(QTabBar):
    """
    A custom QTabBar implementation designed to support right-aligned tab layouts.
    This component is intended to be used within a QTabWidget or a custom layout
    where tab positioning needs to be controlled.
    """

    def __init__(self, parent=None, spacer_index: int | None = None) -> None:
        super().__init__(parent)
        # Hide the built-in scroll/arrows since tabs fit for the current UI
        try:
            # setUsesScrollButtons may not exist in all Qt bindings, guard it
            self.setUsesScrollButtons(False)
        except AttributeError:
            pass
        self.setExpanding(False)
        self._spacer_index = spacer_index

    def setSpacerIndex(self, index: int) -> None:
        self._spacer_index = index
        self.update()

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

        # print(f"DEBUG: spacer_idx={spacer_idx}, count={self.count()}, index={index}")

        if index == spacer_idx:
            # Return a minimal width for the spacer tab so it doesn't influence
            # the overall tab bar sizeHint or force the window to expand.
            return QSize(0, size.height())
        return size
