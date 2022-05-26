import logging
from typing import List
from common.mom.types import RawDataMessage
from common.mom.broker.base import BaseBrokerMOM

LOG_NAME = 'AffinityBrokerMOM'


class AffinityBrokerMOM(BaseBrokerMOM):
    def __init__(self):
        super().__init__(batching=True)

    def __del__(self):
        super().__del__()

    def forward(self, msg: RawDataMessage):
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

    # Base class implementations

    def recv(self) -> RawDataMessage:
        msg = self._recv_data_msg()
        if msg:
            return msg.data

    def _parse_custom_config(self):
        config = super()._parse_custom_config()
        logging.debug(f'[{LOG_NAME}] Parsing custom configuration...')
        inputs = config['inputs']
        self.__parse_inputs(inputs)
        logging.debug(f'[{LOG_NAME}] Custom configuration parsed')

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

    def __forward_msg_rr(self, msg: RawDataMessage):
        assigned_worker = (self._rr_last_sent + 1) % self._count
        self.__forward_to_worker(assigned_worker, msg)
        self._rr_last_sent = assigned_worker

    def __forward_msg_affinity(self, affinity_idx: int, msg: RawDataMessage):
        fields = self._unpack(msg.data)
        affinity_value = fields[affinity_idx]
        assigned_worker = hash(affinity_value) % self._count
        self.__forward_to_worker(assigned_worker, msg)

    def __forward_to_worker(self, worker_idx: int, msg: RawDataMessage):
        pusher = self._pushers[worker_idx]
        logging.debug(f'[{LOG_NAME}] Forwarding to worker #{worker_idx}')
        pusher.send_data_row(msg.as_csv())

    def __broadcast_msg(self, msg: RawDataMessage):
        logging.debug(f'[{LOG_NAME}] Broadcasting msg: "{msg}"')
        for pusher in self._pushers:
            pusher.send_data_row(msg.as_csv())
