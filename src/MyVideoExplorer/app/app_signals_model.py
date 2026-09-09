from dataclasses import dataclass, field
import datetime
from enum import Enum
from typing import Any


class SignalFlow(Enum):
    USER_INPUT = "user_input"
    CONTROLLER_OUTPUT = "controller_output"
    COMPONENT_INTERACTION = "component_interaction"


@dataclass
class SignalPayload:
    """
    A standard wrapper for all signal data, including metadata for
    debugging, logging, and traceability.
    """

    data: Any
    sender: str
    name: str = ""
    description: str = ""
    flow: SignalFlow = SignalFlow.CONTROLLER_OUTPUT
    timestamp: datetime.datetime = field(
        default_factory=datetime.datetime.now(datetime.UTC).astimezone
    )

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "sender": self.sender,
            "description": self.description,
            "flow": self.flow.value,
            "timestamp": self.timestamp.isoformat(timespec="milliseconds"),
            "data": self.data,
        }
