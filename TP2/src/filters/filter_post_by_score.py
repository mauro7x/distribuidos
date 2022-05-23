import logging
from common.filters.custom import Filter
from common.utils import init_log


def post_handler(context, send_fn, data):
    logging.debug(f'Handler called with: {data}')


def avg_score_handler(context, send_fn, data):
    logging.debug(f'Handler called with: {data}')


def main():
    init_log()
    handlers = {
        "post": post_handler,
        "avg_score": avg_score_handler
    }
    context = {}
    filter = Filter(handlers, context)
    filter.run()


if __name__ == '__main__':
    main()
