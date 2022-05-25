import logging
from typing import List
from common.mom.transport import Pusher
from common.mom.types import MessageType, RawDataMessage
from common.utils import read_json
from common.mom.base import BaseMOM
import common.mom.constants as const


LOG_NAME = 'BrokerMOM'


class BrokerMOM(BaseMOM):
    def __init__(self):
        logging.debug(f'[{LOG_NAME}] Initializing...')
        super().__init__()
        self.__eofs_received = 0
        self.__running = True
        logging.debug(f'[{LOG_NAME}] Initialized')

    def __del__(self):
        super().__del__()

    def run(self):
        logging.info(f'[{LOG_NAME}] Running...')
        try:
            self.__run()
        except KeyboardInterrupt:
            logging.info(f'[{LOG_NAME}] Stopped')

    # Base class implementations

    def _parse_custom_config(self):
        logging.debug(f'[{LOG_NAME}] Parsing configuration...')
        config = read_json(const.MIDDLEWARE_CONFIG_FILEPATH)
        self.__count = int(config['count'])
        self.__base_hostname = config['base_hostname']
        assert(self.__count > 1)

        # Strategies
        inputs = config['inputs']
        self.__parse_inputs(inputs)
        self.__rr_last_sent = self.__count - 1

        logging.debug(
            f'[{LOG_NAME}] Configuration: (count={self.__count})')

    def _init_pushers(self):
        self.__pushers: List[Pusher] = []

        for i in range(1, self.__count + 1):
            host = f'{self.__base_hostname}_{i}'
            pusher = Pusher(self._context, self._batch_size, self._protocol)
            pusher.connect(host, self._port)
            self.__pushers.append(pusher)

    def _close_pushers(self):
        for pusher in self.__pushers:
            pusher.close()

    # Private

    def __parse_inputs(self, inputs):
        self.__affinity_idx_by_msg = []
        self.__broadcast_by_msg = []

        for input in inputs:
            affinity_key = input.get('affinity_key')
            if affinity_key:
                fields: List[str] = input['data']
                affinity_idx = fields.index(affinity_key)
            else:
                affinity_idx = None

            if input.get('broadcast'):
                broadcast = True
            else:
                broadcast = False

            self.__affinity_idx_by_msg.append(affinity_idx)
            self.__broadcast_by_msg.append(broadcast)

    def __run(self):
        while self.__running:
            msg = self.__recv()
            if msg:
                self.__forward_msg(msg)
            else:
                self.__broadcast_eof()
                self.__running = False

    def __recv(self) -> RawDataMessage:
        while True:
            msg = self._puller.recv()
            if msg.type == MessageType.EOF.value:
                self.__eofs_received += 1
                if self.__eofs_received == self._sources:
                    self.__eofs_received = 0
                    return None
            elif msg.type == MessageType.DATA.value:
                return msg.data
            else:
                raise Exception('Invalid message received from puller')

    def __forward_msg(self, msg: RawDataMessage):
        try:
            broadcast = self.__broadcast_by_msg[msg.idx]
            affinity_idx = self.__affinity_idx_by_msg[msg.idx]
        except Exception:
            raise Exception(f'Invalid message index received ({msg.idx})')

        if broadcast:
            self.__broadcast_msg(msg)
            return

        if affinity_idx is None:
            self.__forward_msg_rr(msg)
        else:
            self.__forward_msg_affinity(affinity_idx, msg)

    def __forward_msg_rr(self, msg: RawDataMessage):
        assigned_worker = (self.__rr_last_sent + 1) % self.__count
        self.__forward_to_worker(assigned_worker, msg)
        self.__rr_last_sent = assigned_worker

    def __forward_msg_affinity(self, affinity_idx: int, msg: RawDataMessage):
        fields = self._unpack(msg.data)
        affinity_value = fields[affinity_idx]
        assigned_worker = hash(affinity_value) % self.__count
        self.__forward_to_worker(assigned_worker, msg)

    def __forward_to_worker(self, worker_idx: int, msg: RawDataMessage):
        pusher = self.__pushers[worker_idx]
        logging.debug(f'[{LOG_NAME}] Forwarding to worker #{worker_idx}')
        pusher.send_csv(msg.as_csv())

    def __broadcast_msg(self, msg: RawDataMessage):
        logging.debug(f'[{LOG_NAME}] Broadcasting msg: "{msg}"')
        for pusher in self.__pushers:
            pusher.send_csv(msg.as_csv())

    def __broadcast_eof(self):
        logging.debug(f'[{LOG_NAME}] Broadcasting EOF')
        for pusher in self.__pushers:
            pusher.send_eof()
