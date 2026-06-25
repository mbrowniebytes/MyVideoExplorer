from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import Enum

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
    timestamp: datetime = field(default_factory=datetime.now)
