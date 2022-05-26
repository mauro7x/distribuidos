import logging
from common.mom.types import Message
from common.mom.broker.base import BaseBrokerMOM


LOG_NAME = 'RRBrokerMOM'


class RRBrokerMOM(BaseBrokerMOM):
    def __init__(self):
        super().__init__(batching=False)

    def __del__(self):
        super().__del__()

    def forward(self, msg: Message):
        assigned_worker = (self._rr_last_sent + 1) % self._count
        pusher = self._pushers[assigned_worker]
        logging.debug(
            f'[{LOG_NAME}] Forwarding to worker #{assigned_worker} (RR)')
        pusher.send(msg.as_bytes())
        self._rr_last_sent = assigned_worker

    # Base class implementations

    def recv(self) -> Message:
        return self._recv_data_msg()
