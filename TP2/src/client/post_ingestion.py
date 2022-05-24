import logging
import zmq
import csv
import common.mom.constants as const
from common.csv import CSVParser


NAME = '[Post Ingestion]'
SEND_N = 1000000


def read_config():
    return 'purge_post', 3000, 'tcp', SEND_N


def run():
    logging.debug(f'{NAME} --- Started ---')
    host, port, protocol, send_n = read_config()
    context = zmq.Context()
    sender = context.socket(zmq.PUSH)
    sender.connect(f'{protocol}://{host}:{port}')
    parser = CSVParser()

    with open('data/posts.csv') as csv_src:
        reader = csv.reader(csv_src)
        _ = next(reader)  # skip headers
        sent = 0
        for post in reader:
            if sent == send_n:
                break

            post_msg = '0' + const.MSG_SEP + parser.encode(post)
            sender.send_string(post_msg)
            sent += 1

    sender.send_string(const.EOF_MSG)

    logging.debug(f'{NAME} --- Finished ---')
