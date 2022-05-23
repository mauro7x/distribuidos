import logging
from common.filters.custom import Filter
from common.utils import init_log


def post_url_handler(context, send_fn, data):
    logging.debug(f'Handler called with: {data}')


def post_sentiment_handler(context, send_fn, data):
    logging.debug(f'Handler called with: {data}')


def main():
    init_log()
    handlers = {
        "post_url": post_url_handler,
        "post_sentiment": post_sentiment_handler
    }
    context = {}
    filter = Filter(handlers, context)
    filter.run()


if __name__ == '__main__':
    main()
