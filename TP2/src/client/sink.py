import logging
import zmq
from typing import List, NamedTuple
from dataclasses import dataclass
from common.csv import CSVParser
from common.mom.transport import Puller
from common.mom.types import MessageType, RawDataMessage


NAME = '[Sink]'
MEME_OUT_PATH = 'out/client.png'
STUDENT_MEMES_OUT_PATH = 'out/student_memes.txt'


class Config(NamedTuple):
    port: int
    protocol: str
    sources: int


@dataclass
class Context:
    avg_score: float = None
    student_memes_file = None
    best_meme_file = None


def read_config() -> Config:
    return Config(3000, 'tcp', 3)


def handle_results(context: Context):
    # Student memes
    if context.student_memes_file:
        student_memes_msg = \
            f'>>> Student memes list saved to "{STUDENT_MEMES_OUT_PATH}"'
        context.student_memes_file.close()
    else:
        student_memes_msg = '>>> No student memes found!'

    # Best meme
    if context.best_meme_file:
        meme_msg = f'>>> Best meme saved to "{MEME_OUT_PATH}"'
        context.best_meme_file.close()
    else:
        meme_msg = '>>> Best meme not present!'

    # Log results
    logging.info(
        'Finished, results:'
        f'\n>>> Average posts score: {context.avg_score}'
        f'\n{meme_msg}'
        f'\n{student_memes_msg}'
    )


def handle_avg_posts_score(context: Context, values: List[str]):
    context.avg_score = values[0]


def handle_student_meme(context: Context, values: List[str]):
    if not context.student_memes_file:
        context.student_memes_file = open(STUDENT_MEMES_OUT_PATH, 'w')

    student_meme = values[0]
    context.student_memes_file.write(f'{student_meme}\n')


def handle_highest_avg_sentiment_meme(context: Context, data: bytes):
    if not context.best_meme_file:
        context.best_meme_file = open(MEME_OUT_PATH, 'wb')

    context.best_meme_file.write(data)


def run():
    logging.debug(f'{NAME} Started')
    config = read_config()
    context = zmq.Context()
    receiver = Puller(context, config.protocol)
    receiver.bind(config.port)
    parser = CSVParser()
    context = Context()
    data_handlers = [handle_avg_posts_score, handle_student_meme]
    eof_received = 0

    while True:
        msg = receiver.recv()
        if msg.type == MessageType.EOF.value:
            eof_received += 1
            if eof_received == config.sources:
                break
        elif msg.type == MessageType.DATA.value:
            data_msg: RawDataMessage = msg.data
            handler = data_handlers[data_msg.idx]
            values = parser.decode(data_msg.data)
            handler(context, values)
        elif msg.type == MessageType.BYTEARRAY.value:
            handle_highest_avg_sentiment_meme(context, msg.data)
        else:
            raise Exception('Invalid message received from puller')

    handle_results(context)

    logging.debug(f'{NAME} Finished')
