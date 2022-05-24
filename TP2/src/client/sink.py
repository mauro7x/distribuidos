import logging
import zmq
from dataclasses import dataclass
import common.mom.constants as const
from common.csv import CSVParser


NAME = '[Sink]'
OUT_PATH = 'highest_avg_sentiment_meme.png'


@dataclass
class Context:
    avg_score: float = None
    student_memes = []
    best_meme: str = None


def read_config():
    return 3000, 'tcp', 3


def handle_results(context: Context):
    # Save best meme
    # TODO

    # Log
    lines = []
    lines.append('Finished, results:')
    lines.append(f'>>> Average posts score: {context.avg_score}')
    lines.append(f'>>> Best meme saved to "{OUT_PATH}" ({context.best_meme})')
    if len(context.student_memes):
        lines.append('>>> Student-related memes:')
        for meme in context.student_memes:
            lines.append(f'\t- {meme}')
    else:
        lines.append('>>> No student-related memes :(')

    msg = '\n'.join(lines)
    logging.info(msg)


def handle_avg_posts_score(context: Context, values):
    context.avg_score = values[0]


def handle_student_meme(context: Context, values):
    student_meme = values[0]
    context.student_memes.append(student_meme)


def handle_highest_avg_sentiment_meme(context: Context, values):
    context.best_meme = values[0]


def run():
    logging.debug(f'{NAME} --- Started ---')
    port, protocol, sources = read_config()
    context = zmq.Context()
    receiver = context.socket(zmq.PULL)
    receiver.bind(f'{protocol}://*:{port}')
    parser = CSVParser()
    context = Context()
    handlers = {
        "0": handle_avg_posts_score,
        "1": handle_student_meme,
        "2": handle_highest_avg_sentiment_meme
    }
    eof_received = 0

    while True:
        msg = receiver.recv_string()
        if msg == const.EOF_MSG:
            eof_received += 1
            if eof_received == sources:
                break
            else:
                continue

        msg_idx, msg_data = msg.split(const.MSG_SEP, 1)
        handler = handlers[msg_idx]
        values = parser.decode(msg_data)
        handler(context, values)

    handle_results(context)

    logging.debug(f'{NAME} --- Finished ---')
