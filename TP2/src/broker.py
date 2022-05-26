import os
from common.utils import init_log
from common.mom.broker.roundrobin import RRBrokerMOM
from common.mom.broker.affinity import AffinityBrokerMOM
from common.wrapper import BaseWrapper


AFFINITY_ENABLED_ENV_KEY = 'AFFINITY'


class Broker(BaseWrapper):
    def __init__(self):
        super().__init__()
        affinity_env_value = os.getenv(AFFINITY_ENABLED_ENV_KEY, 'false')
        affinity = affinity_env_value.lower() == 'true'
        if affinity:
            self._mom = AffinityBrokerMOM()
        else:
            self._mom = RRBrokerMOM()

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
