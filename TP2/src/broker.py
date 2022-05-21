import logging
from common.utils import init_log


def main():
    init_log('debug')
    logging.info('[Broker] Example broker executed')


if __name__ == '__main__':
    main()
