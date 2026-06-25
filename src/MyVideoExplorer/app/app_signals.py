from PySide6.QtCore import QObject, Signal
from MyVideoExplorer.app.app_signals_model import SignalPayload, SignalFlow
from typing import Any, cast

class SignalRegistry(QObject):
    """
    Centralized registry for all application-level Qt Signals.
    All signals now carry a SignalPayload object.
    """

    METADATA = {
        "sig_root_folder": {"name": "Root Folder Changed", "description": "Emitted when a root folder path is set.", "flow": SignalFlow.CONTROLLER_OUTPUT},
        "sig_root_folders": {"name": "Root Folders Changed", "description": "Emitted when the list of root folders is updated.", "flow": SignalFlow.CONTROLLER_OUTPUT},
        "sig_selected_folder": {"name": "Selected Folder Changed", "description": "Emitted when the selected folder changes.", "flow": SignalFlow.CONTROLLER_OUTPUT},
        "sig_file_changed": {"name": "File Changed", "description": "Emitted when the selected file changes.", "flow": SignalFlow.CONTROLLER_OUTPUT},
        "sig_image_changed": {"name": "Image Changed", "description": "Emitted when the selected image changes.", "flow": SignalFlow.CONTROLLER_OUTPUT},
        "sig_tab_changed": {"name": "Tab Changed", "description": "Emitted when the active tab changes.", "flow": SignalFlow.CONTROLLER_OUTPUT},
    }

    def create_payload(self, signal_name: str, data: Any, sender: str) -> SignalPayload:
        metadata = self.METADATA.get(signal_name, {})
        return SignalPayload(
            data=data,
            sender=sender,
            name=cast(str, metadata.get("name", "")),
            description=cast(str, metadata.get("description", "")),
            flow=cast(SignalFlow, metadata.get("flow", SignalFlow.CONTROLLER_OUTPUT))
        )

    # Folder Management
    sig_root_folder = Signal(object)
    sig_root_folders = Signal(object)
    sig_selected_folder = Signal(object)

    # File/Media Management
    sig_file_changed = Signal(object)
    sig_image_changed = Signal(object)

    # UI State
    sig_tab_changed = Signal(object)
