import logging
from typing import Any, Callable, Dict
from common.mom.worker import WorkerMOM
from common.mom.constants import EOF_MSG_ID
from common.mom.types import Message, Sendable


SendFn = Callable[[Sendable], None]
Context = Any
EofHandler = Callable[[Context, SendFn], None]
MsgHandler = Callable[[Context, SendFn, Any], None]
Handlers = Dict[str, MsgHandler]


class Filter:
    def __init__(self, handlers: Handlers, context: Context = None):
        logging.debug('Initializing Filter...')
        self.__mom = WorkerMOM()
        self.__running = True
        self.__handlers = handlers
        self.__context = context
        self.__eof_handler = None
        logging.debug('Filter initialized')

    def run(self):
        try:
            logging.info('Filter running...')
            while self.__running:
                msg = self.__mom.recv()
                if msg:
                    self.__process_msg(msg)
        except KeyboardInterrupt:
            logging.info('Filter stopped')

    def set_eof_handler(self, eof_handler: EofHandler):
        self.__eof_handler = eof_handler

    # Private

    def __process_msg(self, msg: Message):
        if msg.id in self.__handlers:
            handler = self.__handlers[msg.id]
            handler(self.__context, self.__mom.send, msg.data)
        elif msg.id == EOF_MSG_ID:
            logging.debug('EOF message received, stopping')
            if self.__eof_handler:
                self.__eof_handler(self.__context, self.__mom.send)
            self.__mom.broadcast_eof()
            self.__running = False
        else:
            logging.critical(f"Unknown message received: {msg}")
            exit(-1)
