import logging
from dataclasses import dataclass
from typing import Tuple
from common.filters.custom import Filter
from common.utils import init_log


@dataclass
class Context:
    highest_sent_img: Tuple[str, float] = None


def img_handler(context: Context, _, data):
    logging.debug(f'Handler called with: {data}')
    if not context.highest_sent_img:
        context.highest_sent_img = (data.img_url, data.avg_sentiment)
        return

    _, avg_sentiment = context.highest_sent_img
    if data.avg_sentiment > avg_sentiment:
        context.highest_sent_img = (data.img_url, data.avg_sentiment)


def eof_handler(context: Context, send_fn):
    logging.debug('EOF handler called')
    url, avg_sentiment = context.highest_sent_img

    # TODO: Send binary to client

    # Temp:
    logging.warning(f'Final: (url={url}, avg_sentiment={avg_sentiment})')


def main():
    init_log()
    handlers = {"img": img_handler}
    context = Context()
    filter = Filter(handlers, context)
    filter.set_eof_handler(eof_handler)
    filter.run()


if __name__ == '__main__':
    main()
