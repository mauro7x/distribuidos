import logging
from typing import NamedTuple
import zmq
import csv
import common.mom.constants as const
from common.csv import CSVParser
from common.mom.transport import Pusher


NAME = '[Post Ingestion]'
SEND_N = 1000
PRINT_BETWEEN = 100000
BATCH_SIZE = 1000


class Config(NamedTuple):
    host: str
    port: int
    protocol: str
    send_n: int
    batch_size: int


def read_config() -> Config:
    return Config('purge_post', 3000, 'tcp', SEND_N, BATCH_SIZE)


def run():
    logging.debug(f'{NAME} Started')
    config = read_config()
    context = zmq.Context()
    sender = Pusher(context, config.batch_size, config.protocol)
    sender.connect(config.host, config.port)
    parser = CSVParser()

    with open('data/posts.csv') as csv_src:
        reader = csv.reader(csv_src)
        _ = next(reader)  # skip headers
        sent = 0
        for post in reader:
            if sent % PRINT_BETWEEN == 0:
                logging.info(f'{NAME} Sent: {sent}')

            if config.send_n is not None and sent == config.send_n:
                break

            post_msg = '0' + const.MSG_SEP + parser.encode(post)
            sender.send_csv(post_msg)
            sent += 1

    sender.send_eof()
    logging.info(f'{NAME} Finished')

    # logging.debug(f'{NAME} Finished')
