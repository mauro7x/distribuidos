import logging
from typing import Tuple
import zmq
from abc import ABC
from common.mom.types import Message, MessageType
from common.mom.constants import HWM_ZMQ

LOG_NAME = 'Transport'


class Socket(ABC):
    def __init__(self, protocol: str):
        self.__protocol = protocol
        self._socket = None

    def close(self):
        self._socket.close()

    # Protected

    def _addr(self, host: str, port: int):
        return f'{self.__protocol}://{host}:{port}'


class Pusher(Socket):
    def __init__(self, context: zmq.Context, protocol: str):
        super().__init__(protocol)
        self._socket = context.socket(zmq.PUSH)
        self._socket.set_hwm(HWM_ZMQ)

    def connect(self, host: str, port: int):
        addr = self._addr(host, port)
        logging.debug(f'[{LOG_NAME}] Connecting pusher to {addr}')
        self._socket.connect(addr)

    def send(self, data: bytes):
        self._socket.send(data)

    def send_bytes(self, data: bytes):
        msg = MessageType.BYTEARRAY.value + data
        self._socket.send(msg)

    def send_eof(self):
        self._socket.send(MessageType.EOF.value)


class Puller(Socket):
    def __init__(self, context: zmq.Context, protocol: str):
        super().__init__(protocol)
        self._socket = context.socket(zmq.PULL)
        self._socket.set_hwm(HWM_ZMQ)

    def bind(self, port: int):
        addr = self._addr('*', port)
        logging.debug(f'[{LOG_NAME}] Binding puller to {addr}')
        self._socket.bind(addr)

    def recv(self) -> Message:
        return self._recv_msg()

    # Protected

    def _recv_msg(self) -> Message:
        msg = self._socket.recv()
        type, payload = Puller.parse(msg)
        return Message(type, payload)

    # Static

    @staticmethod
    def parse(msg) -> Tuple[bytes, bytes]:
        return msg[:1], msg[1:]
