import zmq
import json
from typing import List
from common.mom.types import Message, MessageType, RawDataMessage
from common.mom.transport.base import Puller, Pusher


class BatchingPuller(Puller):
    def __init__(self, context: zmq.Context, protocol: str):
        super().__init__(context, protocol)
        self.__buffer: List[Message] = []

    def recv(self) -> Message:
        if len(self.__buffer) == 0:
            self.__recv()

        return self.__buffer.pop()

    # Private

    def __recv(self):
        msg = self._recv_msg()

        if msg.type == MessageType.EOF.value \
                or type == MessageType.BYTEARRAY.value:
            self.__buffer.append(msg)
        elif msg.type == MessageType.DATA.value:
            decoded = msg.data.decode('utf-8')
            batch = json.loads(decoded)
            for data_msg in batch:
                data = RawDataMessage(data_msg)
                msg = Message(type, data)
                self.__buffer.append(msg)
        else:
            raise Exception(f'Unknown message type received: {type}')


class BatchingPusher(Pusher):
    def __init__(self, context: zmq.Context, protocol: str, batch_size: int):
        super().__init__(context, protocol)
        self.__csv_batch_size = batch_size
        self.__csv_batch: List[str] = []

    def send_data_row(self, data: str):
        self.__csv_batch.append(data)
        if len(self.__csv_batch) == self.__csv_batch_size:
            self.__flush_batch()

    def send_eof(self):
        self.__flush_batch()
        self._socket.send(MessageType.EOF.value)

    # Private

    def __flush_batch(self):
        if len(self.__csv_batch) == 0:
            return

        serialized_batch = json.dumps(self.__csv_batch).encode('utf-8')
        msg = MessageType.DATA.value + serialized_batch
        self._socket.send(msg)
        self.__csv_batch = []
