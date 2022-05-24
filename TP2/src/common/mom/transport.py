import logging
import zmq
import json
from typing import List, Tuple
from common.mom.types import Message, MessageType, RawDataMessage


class Socket:
    def __init__(self, protocol: str):
        self.__protocol = protocol

    def _addr(self, host: str, port: int):
        return f'{self.__protocol}://{host}:{port}'


class Pusher(Socket):
    def __init__(self, context: zmq.Context, batch_size: int, protocol=str):
        super().__init__(protocol)
        self.__socket = context.socket(zmq.PUSH)
        self.__csv_batch_size = batch_size
        self.__csv_batch: List[str] = []

    def connect(self, host: str, port: int):
        addr = self._addr(host, port)
        logging.debug(f'Connecting pusher to {addr}')
        self.__socket.connect(addr)

    def send_csv(self, data: str):
        self.__csv_batch.append(data)
        if len(self.__csv_batch) == self.__csv_batch_size:
            self.__flush_batch()

    def send_bytes(self, data: bytes):
        msg = MessageType.BYTEARRAY.value + data
        self.__socket.send(msg)

    def send_eof(self):
        self.__flush_batch()
        self.__socket.send(MessageType.EOF.value)

    # Private

    def __flush_batch(self):
        if len(self.__csv_batch) == 0:
            return

        serialized_batch = json.dumps(self.__csv_batch).encode('utf-8')
        msg = MessageType.DATA.value + serialized_batch
        self.__socket.send(msg)
        self.__csv_batch = []


class Puller(Socket):
    def __init__(self, context: zmq.Context, protocol: str):
        super().__init__(protocol)
        self.__socket = context.socket(zmq.PULL)
        self.__buffer: List[Message] = []

    def bind(self, port: int):
        addr = self._addr('*', port)
        logging.debug(f'Binding puller to {addr}')
        self.__socket.bind(addr)

    def recv(self) -> Message:
        if len(self.__buffer) == 0:
            self.__recv()

        return self.__buffer.pop()

    # Private

    def __recv(self):
        msg = self.__socket.recv()
        type, payload = Puller.__parse(msg)

        if type == MessageType.EOF.value \
                or type == MessageType.BYTEARRAY.value:
            msg = Message(type, payload)
            self.__buffer.append(msg)
        elif type == MessageType.DATA.value:
            decoded = payload.decode('utf-8')
            batch = json.loads(decoded)
            for data_msg in batch:
                data = RawDataMessage(data_msg)
                msg = Message(type, data)
                self.__buffer.append(msg)
        else:
            raise Exception(f'Unknown message type received: {type}')

    # Static

    @staticmethod
    def __parse(msg) -> Tuple[bytes, bytes]:
        return msg[:1], msg[1:]
