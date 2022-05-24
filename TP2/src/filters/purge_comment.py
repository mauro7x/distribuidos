import logging
from common.filter import Filter
from common.utils import init_log


def comment_handler(_, send_fn, data):
    logging.debug(f'Handler called with: {data}')

    if not data.permalink:
        logging.debug('Ignoring comment with null URL')
        return

    if not data.sentiment:
        logging.debug('Ignoring comment with null sentiment')
        return

    if not data.body:
        logging.debug('Ignoring comment with null body')
        return

    send_fn({
        "url": data.permalink,
        "sentiment": data.sentiment,
        "body": data.body
    })


def main():
    init_log()
    handlers = {"comment": comment_handler}
    filter = Filter(handlers)
    filter.run()


if __name__ == '__main__':
    main()
