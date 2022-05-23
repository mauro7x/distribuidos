import logging
from common.filters.custom import Filter
from common.utils import init_log


def comment_handler(context, send_fn, data):
    logging.debug(f'Handler called with: {data}')


def analyzed_post_handler(context, send_fn, data):
    logging.debug(f'Handler called with: {data}')


def main():
    init_log()
    handlers = {
        "comment": comment_handler,
        "analyzed_post": analyzed_post_handler
    }
    context = {}
    filter = Filter(handlers, context)
    filter.run()


if __name__ == '__main__':
    main()
