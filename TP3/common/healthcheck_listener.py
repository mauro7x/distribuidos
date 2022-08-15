import logging
import signal
import zmq


class HealthcheckListener:
    def __init__(self, port: int):
        self.__context = zmq.Context()
        self.__init_server(port)
        self.__init_signal_handlers()

    def __init_server(self, port: int):
        self.__socket = self.__context.socket(zmq.REP)
        self.__socket.bind(f'tcp://*:{port}')
        logging.debug('Healthcheck server socket bound')

    def __init_signal_handlers(self):
        handler = lambda *_: self.stop()
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)

    def run(self):
        logging.info('Running healthcheck server...')
        while True:
            try:
                self.__socket.recv()
                # logging.debug('Ping received')
                self.__socket.send(b'')
            except KeyboardInterrupt:
                break

    def stop(self, code=0):
        self.__context.destroy(0)
        exit(code)
