from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QComboBox, QMenu, QWidget

from MyVideoExplorer.theme.theme import APP_THEME


class _CheckboxCombo(QComboBox):
    """Internal QComboBox subclass that overrides showPopup to display a custom menu."""

    custom_popup = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        APP_THEME.setup_combo_box(self)

    def showPopup(self) -> None:  # type: ignore[override]
        """Emit the custom_popup signal instead of showing the default dropdown."""
        self.custom_popup.emit()


class CheckboxComboBox(QObject):
    """Combo box widget that allows selecting multiple items via checkboxes.

    Emits ``selection_changed`` whenever the set of checked items changes.
    """

    selection_changed = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._combo: _CheckboxCombo = _CheckboxCombo(parent)
        self._combo.custom_popup.connect(self._show_menu)

        self._menu: QMenu = QMenu(self._combo)
        self._actions: dict[str, QAction] = {}
        self._menu.triggered.connect(self._on_triggered)

    @property
    def widget(self) -> QComboBox:
        """Return the underlying QComboBox widget for layout purposes."""
        return self._combo

    def set_items(self, items: list[str]) -> None:
        """Set the list of checkable items.

        Args:
            items: List of item labels.
        """
        self._menu.clear()
        self._actions.clear()
        self._combo.clear()
        for item in items:
            action = QAction(item, self._menu)
            action.setCheckable(True)
            action.setChecked(False)
            self._actions[item] = action
            self._menu.addAction(action)
            self._combo.addItem(item)
        self._update_display()

    def selected_items(self) -> list[str]:
        """Return the list of currently selected (checked) items."""
        return [item for item, action in self._actions.items() if action.isChecked()]

    def select_all(self) -> None:
        """Check all items."""
        for action in self._actions.values():
            action.setChecked(True)
        self._update_display()
        self.selection_changed.emit(list(self._actions.keys()))

    def clear_selection(self) -> None:
        """Uncheck all items."""
        for action in self._actions.values():
            action.setChecked(False)
        self._update_display()
        self.selection_changed.emit([])

    def _show_menu(self) -> None:
        """Show the checkbox menu when the combo box is activated."""
        self._menu.exec(self._combo.mapToGlobal(self._combo.rect().bottomLeft()))

    def _on_triggered(self, action: QAction) -> None:
        """Handle menu item trigger (toggle check state).

        Args:
            action: The triggered QAction.
        """
        self._update_display()
        self.selection_changed.emit(self.selected_items())

    def _update_display(self) -> None:
        """Update the combo box display text based on selected items."""
        selected = self.selected_items()
        if not selected or len(selected) == len(self._actions):
            self._combo.setCurrentText("Any")
        else:
            self._combo.setCurrentText(", ".join(selected))
