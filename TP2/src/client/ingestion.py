import logging
import zmq
import csv
from io import TextIOWrapper
from typing import NamedTuple
import common.mom.constants as const
from common.mom.transport import Pusher
from common.csv import CSVParser


class IngestionConfig(NamedTuple):
    name: str
    src_filepath: str
    host: str
    port: int
    protocol: str
    batch_size: int
    print_info_every_msgs: int
    skip_headers: bool
    limit: int
    msg_idx: int


def run(config: IngestionConfig):
    logging.info(f'[{config.name}] Started')
    zmq_context = zmq.Context()
    pusher = Pusher(zmq_context, config.batch_size, config.protocol)
    pusher.connect(config.host, config.port)

    # Send data
    with open(config.src_filepath) as file:
        send(file, pusher, config)
    pusher.send_eof()

    logging.info(f'[{config.name}] Finished')


def send(file: TextIOWrapper, pusher: Pusher, config: IngestionConfig):
    parser = CSVParser()
    reader = csv.reader(file)
    if config.skip_headers:
        _ = next(reader)

    msgs_sent = 0
    for data in reader:
        if config.print_info_every_msgs \
                and msgs_sent % config.print_info_every_msgs == 0:
            logging.info(f'[{config.name}] Sent: {msgs_sent}')

        if config.limit and msgs_sent >= config.limit:
            break

        encoded = parser.encode(data)
        msg = f'{config.msg_idx}{const.MSG_SEP}{encoded}'
        pusher.send_csv(msg)
        msgs_sent += 1
