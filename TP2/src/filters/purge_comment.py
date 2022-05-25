import logging
from common.filter import BaseFilter
from common.utils import init_log


class Filter(BaseFilter):
    def __init__(self):
        super().__init__()
        self._handlers = {
            "comment": self.__comment_handler
        }

    def __comment_handler(self, data):
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

        self._send({
            "url": data.permalink,
            "sentiment": data.sentiment,
            "body": data.body
        })


def main():
    init_log()
    filter = Filter()
    filter.run()


if __name__ == '__main__':
    main()
