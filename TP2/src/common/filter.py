import logging
from common.mom.types import DataMessage
from common.mom.worker import WorkerMOM
from common.wrapper import BaseWrapper


LOG_NAME = 'BaseFilter'


class BaseFilter(BaseWrapper):
    def __init__(self):
        super().__init__()
        self._mom = WorkerMOM()
        self._handlers = {}

    # Base class implementations

    def _handle_msg(self, msg: DataMessage):
        if msg.id in self._handlers:
            handler = self._handlers[msg.id]
            logging.debug(f'Invoking message handler with: {msg.data}')
            handler(msg.data)
        else:
            raise Exception(f'No handler found for msg: {msg}')

    def _handle_eof(self):
        self._eof_handler()
        self._mom.broadcast_eof()

    # Protected

    def _send(self, data):
        send_fn = self._mom.send_bytes \
            if isinstance(data, bytes) \
            else self._mom.send_csv
        send_fn(data)

    def _eof_handler(self):
        pass
