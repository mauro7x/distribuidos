from abc import ABC, abstractclassmethod
from typing import List
import zmq
import logging
import common.mom.constants as const
from common.mom.transport import Puller
from common.utils import read_json
from common.csv import CSVParser


class BaseMOM(ABC):
    def __init__(self):
        self._context: zmq.Context = zmq.Context()
        self.__parse_config()
        self.__csv_parser = CSVParser()

        # Init zmq pullers and pushers
        self.__init_puller()
        self._init_pushers()

    def __del__(self):
        self._context.destroy(-1)

    # Protected

    @abstractclassmethod
    def _parse_custom_config(self):
        pass

    @abstractclassmethod
    def _init_pushers(self):
        pass

    def _pack(self, values: List[str]):
        return self.__csv_parser.encode(values)

    def _unpack(self, csv_line: str):
        return self.__csv_parser.decode(csv_line)

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
            'BaseMOM configuration:'
            f'\nPort: {self._port}'
            f'\nProtocol: {self._protocol}'
            f'\nSources: {self._sources}'
            f'\nBatch size: {self._batch_size}'
        )

    def __init_puller(self):
        self._puller = Puller(self._context, self._protocol)
        self._puller.bind(self._port)
