import logging
from typing import Any, Callable, Dict
from common.mom.worker import WorkerMOM
from common.mom.constants import EOF_MSG_ID
from common.mom.types import Message, Sendable


SendFn = Callable[[Sendable], None]
Context = Dict[str, Any]
Handler = Callable[[Context, SendFn, Any], None]
Handlers = Dict[str, Handler]


class Filter:
    def __init__(self, handlers: Handlers, context: Context):
        logging.debug('Initializing Filter...')
        self.__mom = WorkerMOM()
        self.__running = True
        self.__handlers = handlers
        self.__context = context
        logging.debug('Filter initialized')

    def run(self):
        try:
            logging.info('Filter running...')
            while self.__running:
                msg = self.__mom.recv()
                self.__process_msg(msg)
        except KeyboardInterrupt:
            logging.info('Filter stopped')

    # Private

    def __process_msg(self, msg: Message):
        if msg.id in self.__handlers:
            handler = self.__handlers[msg.id]
            handler(self.__context, self.__mom.send, msg.data)
        elif msg.id == EOF_MSG_ID:
            logging.info('EOF message received')
            self.__running = False
            self.__mom.broadcast_eof()
        else:
            logging.critical(f"Unknown message received: {msg}")
            exit(-1)
