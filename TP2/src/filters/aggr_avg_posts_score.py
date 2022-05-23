import logging
from dataclasses import dataclass
from common.filters.custom import Filter
from common.types import Average
from common.utils import init_log


@dataclass
class Context:
    avg = Average()


def score_handler(context: Context, _, data):
    logging.debug(f'Handler called with: {data}')
    score = int(data.score)
    context.avg.add(score)


def eof_handler(context: Context, send_fn):
    logging.debug('EOF handler called')
    send_fn({"avg_score": context.avg.get()})

    # Temp:
    logging.info(
        f'Final: (avg: {context.avg.get()}, count: {len(context.avg)})')


def main():
    init_log()
    handlers = {"score": score_handler}
    context = Context()
    filter = Filter(handlers, context)
    filter.set_eof_handler(eof_handler)
    filter.run()


if __name__ == '__main__':
    main()
