from common.mom.broker import BrokerMOM
from common.utils import init_log


def main():
    init_log()
    mom = BrokerMOM()
    mom.run()


if __name__ == '__main__':
    main()
