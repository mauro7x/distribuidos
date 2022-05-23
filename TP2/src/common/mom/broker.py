import zmq
import logging
from typing import List
from common.utils import read_json, hash
from common.mom.base import BaseMOM
import common.mom.constants as const


class BrokerMOM(BaseMOM):
    def __init__(self):
        super().__init__()
        self.__eofs_received = 0

    def run(self):
        logging.info('Broker running...')
        try:
            self.__run()
        except KeyboardInterrupt:
            logging.info('Broker stopped')

    # Base class implementations

    def _parse_custom_config(self):
        logging.debug('Parsing broker configuration...')
        config = read_json(const.MIDDLEWARE_CONFIG_FILEPATH)
        self.__count = int(config['count'])
        self.__base_hostname = config['base_hostname']
        assert(self.__count > 1)

        # Strategies
        inputs = config['inputs']
        self.__affinity_idx_by_msg = \
            BrokerMOM.__parse_inputs(inputs)
        self.__rr_last_sent = self.__count - 1

        logging.debug('MOM broker configuration: (count={self.__count})')

    def _init_pushers(self):
        self.__pushers: List[zmq.Socket] = []

        for i in range(1, self.__count + 1):
            host = f'{self.__base_hostname}_{i}'
            pusher = self._context.socket(zmq.PUSH)
            addr = self._addr(host)
            logging.debug(f'Connecting pusher to {addr}')
            pusher.connect(addr)
            self.__pushers.append(pusher)

    # Private

    def __run(self):
        while True:
            msg = self._puller.recv_string()

            if msg == const.EOF_MSG:
                self.__eofs_received += 1
                if self.__eofs_received == self._sources:
                    self.__broadcast_eof()
                    break
            else:
                logging.debug(f"Received: '{msg}'")
                self.__forward_msg(msg)

    def __broadcast_eof(self):
        logging.debug('Broadcasting EOF')
        for pusher in self.__pushers:
            pusher.send_string(const.EOF_MSG)

    def __forward_msg(self, msg: str):
        msg_idx, _ = msg.split(const.MSG_SEP, 1)

        try:
            affinity_idx = self.__affinity_idx_by_msg[int(msg_idx)]
        except Exception:
            error = f'Invalid message index received ({msg_idx})'
            logging.critical(error)
            raise Exception(error)

        if affinity_idx is None:
            self.__forward_msg_rr(msg)
        else:
            self.__forward_msg_affinity(affinity_idx, msg)

    def __forward_msg_rr(self, msg: str):
        assigned_worker = (self.__rr_last_sent + 1) % self.__count
        self.__forward_to_worker(assigned_worker, msg)
        self.__rr_last_sent = assigned_worker

    def __forward_msg_affinity(self, affinity_idx: int, msg: str):
        _, msg_data = msg.split(const.MSG_SEP, 1)
        fields = self._unpack(msg_data)
        affinity_value = fields[affinity_idx]
        assigned_worker = hash(affinity_value) % self.__count
        self.__forward_to_worker(assigned_worker, msg)

    def __forward_to_worker(self, worker_idx: int, msg: str):
        pusher = self.__pushers[worker_idx]
        logging.debug(f'Forwarding to worker #{worker_idx}')
        pusher.send_string(msg)

    # Static

    @staticmethod
    def __parse_inputs(inputs):
        affinity_idx_by_msg = []
        for input in inputs:
            affinity_key = input.get('affinity_key')
            if affinity_key:
                fields: List[str] = input['data']
                affinity_idx = fields.index(affinity_key)
                affinity_idx_by_msg.append(affinity_idx)
            else:
                affinity_idx_by_msg.append(None)

        return affinity_idx_by_msg
