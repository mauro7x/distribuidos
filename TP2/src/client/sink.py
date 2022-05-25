import logging
import os
import zmq
from typing import List, NamedTuple
from dataclasses import dataclass
from common.csv import CSVParser
from common.mom.transport import Puller
from common.mom.types import MessageType, RawDataMessage


NAME = '[Sink]'
OUT_DIRPATH = 'out'
TEMP_MEME_FILEPATH = f'{OUT_DIRPATH}/best_meme.downloading'
FINAL_MEME_FILENAME = f'{OUT_DIRPATH}/best_meme'
STUDENT_MEMES_FILEPATH = f'{OUT_DIRPATH}/student_memes.txt'


class Config(NamedTuple):
    port: int
    protocol: str
    sources: int


@dataclass
class Context:
    avg_score: float = None
    student_memes_file = None
    best_meme_file = None
    file_extension = None


def read_config() -> Config:
    return Config(3000, 'tcp', 3)


def handle_results(context: Context):
    # Student memes
    if context.student_memes_file:
        student_memes_msg = \
            f'>>> Student memes list saved to "{STUDENT_MEMES_FILEPATH}"'
        context.student_memes_file.close()
    else:
        student_memes_msg = '>>> No student memes found!'

    # Best meme
    if context.best_meme_file and context.file_extension:
        context.best_meme_file.close()
        final_filepath = f'{FINAL_MEME_FILENAME}{context.file_extension}'
        os.rename(TEMP_MEME_FILEPATH, final_filepath)
        meme_msg = f'>>> Best meme saved to "{final_filepath}"'
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
        context.student_memes_file = open(STUDENT_MEMES_FILEPATH, 'w')

    student_meme = values[0]
    context.student_memes_file.write(f'{student_meme}\n')


def handle_file_extension(context: Context, values: List[str]):
    context.file_extension = values[0]


def handle_highest_avg_sentiment_meme(context: Context, data: bytes):
    if not context.best_meme_file:
        context.best_meme_file = open(TEMP_MEME_FILEPATH, 'wb')

    context.best_meme_file.write(data)


def run():
    logging.debug(f'{NAME} Started')
    config = read_config()
    context = zmq.Context()
    receiver = Puller(context, config.protocol)
    receiver.bind(config.port)
    parser = CSVParser()
    context = Context()
    data_handlers = [
        handle_avg_posts_score,
        handle_student_meme,
        handle_file_extension
    ]
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
