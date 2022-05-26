import logging
from typing import List
from abc import abstractclassmethod
import common.mom.constants as const
from common.mom.transport.base import Pusher as SimplePusher
from common.mom.transport.batching import BatchingPusher
from common.mom.base import BaseMOM
from common.utils import read_json

LOG_NAME = 'BrokerMOM'


class BaseBrokerMOM(BaseMOM):
    def __init__(self, batching: bool):
        super().__init__(batching)

    def __del__(self):
        super().__del__()

    @abstractclassmethod
    def forward(self, msg):
        pass

    def broadcast_eof(self):
        logging.debug(f'[{LOG_NAME}] Broadcasting EOF')
        for pusher in self._pushers:
            pusher.send_eof()

    # Base class implementations

    def _parse_custom_config(self):
        logging.debug(f'[{LOG_NAME}] Parsing common configuration...')
        config = read_json(const.MIDDLEWARE_CONFIG_FILEPATH)
        self.__base_hostname = config['base_hostname']
        self._count = int(config['count'])
        self._rr_last_sent = self._count - 1
        assert(self._count > 1)
        logging.debug(
            f'[{LOG_NAME}] Common configuration: (count={self._count})')
        return config

    def _init_pushers(self, batching: bool):
        PusherClass = BatchingPusher if batching else SimplePusher
        args = (self._context, self._protocol, self._batch_size) \
            if batching else (self._context, self._protocol)
        self._pushers: List[PusherClass] = []

        for i in range(1, self._count + 1):
            host = f'{self.__base_hostname}_{i}'
            pusher = PusherClass(*args)
            pusher.connect(host, self._port)
            self._pushers.append(pusher)

    def _close_pushers(self):
        for pusher in self._pushers:
            pusher.close()
