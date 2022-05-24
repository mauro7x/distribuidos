import logging
import requests
import mimetypes
from dataclasses import dataclass
from typing import Tuple
from common.filter import Filter
from common.utils import init_log


DOWNLOADED_FILEPATH = '/tmp/downloaded.png'
CHUNK_SIZE = 1024


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
    if not context.highest_sent_img:
        logging.warning('Final: no image!')
        return

    url, _ = context.highest_sent_img
    response = requests.get(url, stream=True)
    status = response.status_code
    if status != 200:
        logging.warning(f'Could not download image (status: {status})')
        return

    content_type = response.headers['content-type']
    extension = mimetypes.guess_extension(content_type)
    logging.warning(f'URL: {url} | Extension: {extension}')
    for chunk in response.iter_content(CHUNK_SIZE):
        send_fn(chunk)


def main():
    init_log()
    handlers = {"img": img_handler}
    context = Context()
    filter = Filter(handlers, context)
    filter.set_eof_handler(eof_handler)
    filter.run()


if __name__ == '__main__':
    main()
