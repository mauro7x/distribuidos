import logging
from common.filter import Filter
from common.utils import init_log


def post_handler(_, send_fn, data):
    logging.debug(f'Handler called with: {data}')

    if not data.id:
        logging.debug('Ignoring post with null id')
        return

    if not data.url:
        logging.debug('Ignoring post with null URL')
        return

    if not data.score:
        logging.debug('Ignoring post with null score')
        return

    send_fn({
        "p_id": data.id,
        "img_url": data.url,
        "score": data.score
    })


def main():
    init_log()
    handlers = {"post": post_handler}
    filter = Filter(handlers)
    filter.run()


if __name__ == '__main__':
    main()
