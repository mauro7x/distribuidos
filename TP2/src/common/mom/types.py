from typing import Any, Dict, NamedTuple


Sendable = Dict[str, Any]
Data = Any


class Message(NamedTuple):
    id: str
    data: Data


class Input(NamedTuple):
    id: str
    data: Data


class Output(NamedTuple):
    host: str
    msg_idx: int
    data: Data
