import logging
from abc import ABC, abstractclassmethod
import signal
from common.mom.worker import BaseMOM
from common.utils import sigterm_handler


class BaseWrapper(ABC):
    def __init__(self):
        logging.debug('Initializing...')
        self.__running = True
        self._mom: BaseMOM = None
        logging.debug('Initialized')

    def run(self):
        signal.signal(signal.SIGTERM, sigterm_handler)
        try:
            logging.info('Running...')
            while self.__running:
                msg = self._mom.recv()
                if msg:
                    self._handle_msg(msg)
                else:
                    self._handle_eof()
                    self.__running = False
        except KeyboardInterrupt:
            self._mom.stop()

    # Protected

    @abstractclassmethod
    def _handle_msg(self, msg):
        pass

    @abstractclassmethod
    def _handle_eof(self):
        pass
