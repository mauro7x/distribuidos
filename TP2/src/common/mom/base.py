from abc import ABC, abstractclassmethod
import zmq
import logging
import common.mom.constants as const
from common.utils import read_json


class BaseMOM(ABC):
    def __init__(self):
        logging.debug('Initializing BaseMOM...')
        self._context: zmq.Context = zmq.Context()
        self.__parse_config()

        # Init zmq pullers and pushers
        logging.debug('Initializing puller...')
        self.__init_puller()
        logging.debug('Initializing pushers...')
        self._init_pushers()

        logging.debug('BaseMOM initialized')

    def __del__(self):
        self._context.destroy(linger=0)

    # Protected

    @abstractclassmethod
    def _parse_custom_config(self):
        pass

    @abstractclassmethod
    def _init_pushers(self):
        pass

    def _addr(self, host: str):
        return f'{self.__protocol}://{host}:{self.__port}'

    # Private

    def __parse_config(self):
        try:
            self.__parse_common_config()
            self._parse_custom_config()
        except Exception:
            raise Exception('Invalid config file')

    def __parse_common_config(self):
        logging.debug('Parsing common configuration...')
        config = read_json(const.COMMON_CONFIG_FILEPATH)
        self.__port = int(config['port'])
        self.__protocol: str = config['protocol']
        logging.debug(
            'MOM common configuration: '
            f'(protocol={self.__protocol}, port={self.__port})')

    def __init_puller(self):
        puller = self._context.socket(zmq.PULL)
        addr = self._addr('*')
        logging.debug(f'Binding puller to {addr}')
        puller.bind(addr)
        self._puller = puller
