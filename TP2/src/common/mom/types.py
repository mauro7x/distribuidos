from typing import Any, Dict, NamedTuple
from enum import Enum
import common.mom.constants as const


Sendable = Dict[str, Any]
Data = Any


class MessageType(Enum):
    EOF = b'0'
    DATA = b'1'
    BYTEARRAY = b'2'


class Message(NamedTuple):
    type: MessageType
    data: Any


class RawDataMessage:
    def __init__(self, raw_data: str):
        idx, data = raw_data.split(const.MSG_SEP, 1)
        self.idx = int(idx)
        self.data = data

    def as_csv(self) -> str:
        return f'{self.idx}{const.MSG_SEP}{self.data}'


class DataMessage(NamedTuple):
    id: str
    data: Any


class Input(NamedTuple):
    id: str
    data: Data


class Output(NamedTuple):
    host: str
    msg_idx: int
    data: Data | Any
