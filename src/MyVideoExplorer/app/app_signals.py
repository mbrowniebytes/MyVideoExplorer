from typing import Any, cast, ClassVar

from PySide6.QtCore import QObject, Signal

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload


class SignalRegistry(QObject):
    """
    Centralized registry for all application-level Qt signals.

    Signal names intentionally use domain-oriented, readable identifiers rather
    than generic "sig_*" names so they make sense when debugging or wiring
    components together.
    """

    METADATA: ClassVar[dict[str, Any]] = {
        "root_folder_changed": {
            "name": "Root Folder Changed",
            "description": "Emitted when the root folder is changed.",
            "flow": SignalFlow.CONTROLLER_OUTPUT,
        },
        "root_folders_changed": {
            "name": "Root Folders Changed",
            "description": "Emitted when the list of root folders is updated.",
            "flow": SignalFlow.CONTROLLER_OUTPUT,
        },
        "selected_folder_changed": {
            "name": "Selected Folder Changed",
            "description": "Emitted when the selected folder changes.",
            "flow": SignalFlow.CONTROLLER_OUTPUT,
        },
        "file_changed": {
            "name": "File Changed",
            "description": "Emitted when the selected file changes.",
            "flow": SignalFlow.CONTROLLER_OUTPUT,
        },
        "image_changed": {
            "name": "Image Changed",
            "description": "Emitted when the selected image changes.",
            "flow": SignalFlow.CONTROLLER_OUTPUT,
        },
        "tab_changed": {
            "name": "Tab Changed",
            "description": "Emitted when the active tab changes.",
            "flow": SignalFlow.CONTROLLER_OUTPUT,
        },
    }

    # Folder management
    root_folder_changed = Signal(object)
    root_folders_changed = Signal(object)
    selected_folder_changed = Signal(object)

    # File/media management
    file_changed = Signal(object)
    image_changed = Signal(object)

    # UI state
    tab_changed = Signal(object)

    def create_payload(self, signal_name: str, data: Any, sender: str) -> SignalPayload:
        metadata = self.METADATA.get(signal_name, {})
        return SignalPayload(
            data=data,
            sender=sender,
            name=cast(str, metadata.get("name", signal_name)),
            description=cast(str, metadata.get("description", "")),
            flow=cast(SignalFlow, metadata.get("flow", SignalFlow.CONTROLLER_OUTPUT)),
        )

    def emit_payload(self, signal_name: str, data: Any, sender: str) -> None:
        if not hasattr(self, signal_name):
            raise ValueError(f"Unknown application signal: '{signal_name}'")
        payload = self.create_payload(signal_name, data, sender)
        getattr(self, signal_name).emit(payload)
