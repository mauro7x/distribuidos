import logging
import requests
import mimetypes
from typing import Tuple
from common.filter import BaseFilter
from common.utils import init_log


DOWNLOADED_FILEPATH = '/tmp/downloaded.png'
CHUNK_SIZE = 1024


class Filter(BaseFilter):
    def __init__(self):
        super().__init__()
        self._handlers = {
            "img": self.__img_handler
        }
        self.__highest_sent_img: Tuple[str, float] = None

    def __img_handler(self, data):
        logging.debug(f'Handler called with: {data}')
        if not self.__highest_sent_img:
            self.__highest_sent_img = (data.img_url, data.avg_sentiment)
            return

        _, avg_sentiment = self.__highest_sent_img
        if data.avg_sentiment > avg_sentiment:
            self.__highest_sent_img = (data.img_url, data.avg_sentiment)

    def _eof_handler(self):
        logging.debug('EOF handler called')
        if not self.__highest_sent_img:
            logging.warning('Final: no image!')
            return

        url, _ = self.__highest_sent_img
        response = requests.get(url, stream=True)
        status = response.status_code
        if status != 200:
            logging.warning(f'Could not download image (status: {status})')
            return

        content_type = response.headers['content-type']
        extension = mimetypes.guess_extension(content_type)
        logging.warning(f'URL: {url} | Extension: {extension}')
        for chunk in response.iter_content(CHUNK_SIZE):
            self._send(chunk)


def main():
    init_log()
    filter = Filter()
    filter.run()


if __name__ == '__main__':
    main()
