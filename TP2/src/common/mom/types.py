from dataclasses import dataclass
from typing import Any, Dict


Sendable = Dict[str, Any]
Data = Any


@dataclass
class Message:
    id: str
    data: Data


@dataclass
class Input:
    id: str
    data: Data


@dataclass
class Output:
    host: str
    msg_idx: int
    data: Data
