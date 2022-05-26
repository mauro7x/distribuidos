from common.utils import init_log
from common.mom.broker import BrokerMOM
from common.wrapper import BaseWrapper


class Broker(BaseWrapper):
    def __init__(self):
        super().__init__()
        self._mom = BrokerMOM()

    # Base class implementations

    def _handle_msg(self, msg):
        self._mom.forward(msg)

    def _handle_eof(self):
        self._mom.broadcast_eof()


def main():
    init_log()
    broker = Broker()
    broker.run()


if __name__ == '__main__':
    main()
