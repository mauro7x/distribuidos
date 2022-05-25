import logging
from typing import Any, Callable, Dict
from common.mom.worker import WorkerMOM
from common.mom.types import DataMessage, Sendable


SendFn = Callable[[Sendable], None]
Context = Any
EofHandler = Callable[[Context, SendFn], None]
MsgHandler = Callable[[Context, SendFn, Any], None]
Handlers = Dict[str, MsgHandler]


class BaseFilter():
    def __init__(self):
        logging.debug('Initializing Filter...')
        self.__mom = WorkerMOM()
        self.__running = True
        self._handlers = {}
        logging.debug('Filter initialized')

    def run(self):
        try:
            logging.info('Filter running...')
            while self.__running:
                msg = self.__mom.recv()
                if msg:
                    self.__process_msg(msg)
                else:
                    self.__handle_eof()

        except KeyboardInterrupt:
            logging.info('Filter stopped')

    # Abstract

    def _eof_handler(self):
        return

    # Protected

    def _send(self, data):
        send_fn = self.__mom.send_bytes \
            if isinstance(data, bytes) \
            else self.__mom.send_csv
        send_fn(data)

    # Private

    def __process_msg(self, msg: DataMessage):
        if msg.id in self._handlers:
            handler = self._handlers[msg.id]
            handler(msg.data)
        else:
            raise Exception(f'No handler found for msg: {msg}')

    def __handle_eof(self):
        self._eof_handler()
        self.__mom.broadcast_eof()
        self.__running = False
