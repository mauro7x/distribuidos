import logging
import zmq
import csv
import common.mom.constants as const
from common.csv import CSVParser


NAME = '[Comment Ingestion]'
SEND_N = 1000000
print_between = 10000


def read_config():
    return 'purge_comment', 3000, 'tcp', SEND_N


def run():
    logging.debug(f'{NAME} --- Started ---')
    host, port, protocol, send_n = read_config()
    context = zmq.Context()
    sender = context.socket(zmq.PUSH)
    sender.connect(f'{protocol}://{host}:{port}')
    parser = CSVParser()

    with open('data/comments.csv') as csv_src:
        reader = csv.reader(csv_src)
        _ = next(reader)  # skip headers
        sent = 0
        for comment in reader:
            if sent % print_between == 0:
                logging.info(f'{NAME} Sent {sent}')

            if sent == send_n:
                break

            comment_msg = '0' + const.MSG_SEP + parser.encode(comment)
            sender.send_string(comment_msg)
            sent += 1

    sender.send_string(const.EOF_MSG)

    logging.debug(f'{NAME} --- Finished ---')
