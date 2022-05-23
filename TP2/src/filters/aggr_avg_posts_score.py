import logging
from dataclasses import dataclass
from common.filters.custom import Filter
from common.utils import init_log


@dataclass
class Context:
    count: int = 0
    avg: float = 0.0


def score_handler(context: Context, _, data):
    logging.debug(f'Handler called with: {data}')
    score = int(data.score)

    context.count += 1
    context.avg = (context.avg * (1 - (1 / context.count)) +
                   (score / context.count))


def eof_handler(context: Context, send_fn):
    logging.debug('EOF handler called')
    send_fn({"avg_score": context.avg})

    # Temp:
    print('Final:')
    print('- AVG:', context.avg)
    print('- Count:', context.count)


def main():
    init_log()
    handlers = {"score": score_handler}
    context = Context()
    filter = Filter(handlers, context)
    filter.set_eof_handler(eof_handler)
    filter.run()


if __name__ == '__main__':
    main()
