from abc import ABC, abstractclassmethod
from typing import List
import zmq
import logging
import common.mom.constants as const
from common.mom.transport.base import Puller as SimplePuller
from common.mom.transport.batching import BatchingPuller
from common.mom.types import Message, MessageType
from common.utils import read_json
from common.csv import CSVParser


LOG_NAME = 'BaseMOM'


class BaseMOM(ABC):
    def __init__(self, batching=True):
        self._context: zmq.Context = zmq.Context()
        self.__parse_config()
        self.__csv_parser = CSVParser()
        self.__eofs_received = 0

        # Init zmq pullers and pushers
        self.__init_puller(batching)
        self._init_pushers(batching)

    def __del__(self):
        self._puller.close()
        self._close_pushers()
        self._context.term()

    @abstractclassmethod
    def recv(self):
        pass

    def stop(self):
        self._context.destroy(0)

    # Protected

    @abstractclassmethod
    def _parse_custom_config(self):
        pass

    @abstractclassmethod
    def _init_pushers(self, batching: bool):
        pass

    @abstractclassmethod
    def _close_pushers(self):
        pass

    def _pack(self, values: List[str]):
        return self.__csv_parser.encode(values)

    def _unpack(self, csv_line: str):
        return self.__csv_parser.decode(csv_line)

    def _recv_data_msg(self) -> Message:
        while True:
            msg = self._puller.recv()
            if msg.type == MessageType.DATA.value:
                return msg
            elif msg.type == MessageType.EOF.value:
                self.__eofs_received += 1
                if self.__eofs_received == self._sources:
                    self.__eofs_received = 0
                    return None
            else:
                raise Exception('Invalid message received from puller')

    # Private

    def __parse_config(self):
        try:
            self.__parse_common_config()
            self._parse_custom_config()
        except Exception:
            raise Exception('Invalid config file')

    def __parse_common_config(self):
        config = read_json(const.COMMON_CONFIG_FILEPATH)
        self._port = int(config['port'])
        self._protocol: str = config['protocol']
        self._sources = int(config['sources'])
        self._batch_size = int(config['batch_size'])
        logging.debug(
            f'[{LOG_NAME}] configuration:'
            f'\nPort: {self._port}'
            f'\nProtocol: {self._protocol}'
            f'\nSources: {self._sources}'
            f'\nBatch size: {self._batch_size}'
        )

    def __init_puller(self, batching: bool):
        PullerFactory = BatchingPuller if batching else SimplePuller
        self._puller = PullerFactory(self._context, self._protocol)
        self._puller.bind(self._port)
