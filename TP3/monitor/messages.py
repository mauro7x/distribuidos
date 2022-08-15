from dataclasses import dataclass
from typing import Optional
from enum import Enum


class MessageType(Enum):
    EOF = 0
    DEAD_NODE = 1
    NODE_RESET = 2
    FAILED = 3


@dataclass
class Message():
    type: MessageType
    payload: Optional[str]
