import logging
from typing import Any, Callable, Dict
from common.mom.worker import WorkerMOM
from common.mom.types import DataMessage, Sendable


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
                else:
                    self.__handle_eof()
        except KeyboardInterrupt:
            logging.info('Filter stopped')
        except Exception as e:
            logging.critical(e)
            exit(-1)

    def set_eof_handler(self, eof_handler: EofHandler):
        self.__eof_handler = eof_handler

    # Private

    def __process_msg(self, msg: DataMessage):
        if msg.id in self.__handlers:
            handler = self.__handlers[msg.id]
            handler(self.__context, self.__send, msg.data)
        else:
            raise Exception(f'No handler found for msg: {msg}')

    def __handle_eof(self):
        if self.__eof_handler:
            self.__eof_handler(self.__context, self.__send)
        self.__mom.broadcast_eof()
        self.__running = False

    def __send(self, data):
        send_fn = self.__mom.send_bytes \
            if isinstance(data, bytes) \
            else self.__mom.send_csv
        send_fn(data)
