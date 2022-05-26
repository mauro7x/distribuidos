import logging
import os
import zmq
import signal
from typing import List, NamedTuple
from dataclasses import dataclass
from constants import DEFAULT_EXTENSION
from common.csv import CSVParser
from common.mom.transport.batching import BatchingPuller as Puller
from common.mom.types import MessageType, RawDataMessage
from common.utils import sigterm_handler

NAME = '[Sink]'
OUT_DIRPATH = 'out'
TEMP_MEME_FILEPATH = f'{OUT_DIRPATH}/best_meme.downloading'
FINAL_MEME_FILENAME = f'{OUT_DIRPATH}/best_meme'
STUDENT_MEMES_FILEPATH = f'{OUT_DIRPATH}/student_memes.txt'


class SinkConfig(NamedTuple):
    name: str
    port: int
    protocol: str
    sources: int


@dataclass
class Context:
    avg_score: float = None
    student_memes_file = None
    best_meme_file = None
    file_extension = None


def handle_results(context: Context, stopped=False):

    # Student memes
    if context.student_memes_file:
        context.student_memes_file.close()
        student_memes_msg = \
            f'>>> Student memes list saved to "{STUDENT_MEMES_FILEPATH}"'
    else:
        student_memes_msg = '>>> No student memes found!'

    # Best meme
    if context.best_meme_file:
        context.best_meme_file.close()
        extension = context.file_extension \
            if context.file_extension else DEFAULT_EXTENSION
        final_filepath = f'{FINAL_MEME_FILENAME}{extension}'
        os.rename(TEMP_MEME_FILEPATH, final_filepath)
        meme_msg = f'>>> Best meme saved to "{final_filepath}"'
    else:
        meme_msg = '>>> Best meme not present!'

    if stopped:
        logging.warn('Stopped')
        return

    # Log results
    logging.info(
        f'Finished, results:'
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


def run(config: SinkConfig):
    signal.signal(signal.SIGTERM, sigterm_handler)
    logging.debug(f'[{config.name}] Started')
    zmq_context = zmq.Context()
    puller = Puller(zmq_context, config.protocol)
    puller.bind(config.port)
    context = Context()
    handlers = [
        handle_avg_posts_score,
        handle_student_meme,
        handle_file_extension
    ]

    stopped = False
    try:
        process_msgs(puller, context, handlers, config)
    except KeyboardInterrupt:
        stopped = True
        zmq_context.destroy(0)
    finally:
        handle_results(context, stopped)

    logging.debug(f'[{config.name}] Finished')


def process_msgs(
    puller: Puller,
    context: Context,
    handlers,
    config: SinkConfig
):
    parser = CSVParser()
    eof_received = 0

    while True:
        msg = puller.recv()
        if msg.type == MessageType.EOF.value:
            eof_received += 1
            if eof_received == config.sources:
                break
        elif msg.type == MessageType.DATA.value:
            data_msg: RawDataMessage = msg.data
            handler = handlers[data_msg.idx]
            values = parser.decode(data_msg.data)
            handler(context, values)
        elif msg.type == MessageType.BYTEARRAY.value:
            handle_highest_avg_sentiment_meme(context, msg.data)
        else:
            raise Exception('Invalid message received from puller')
