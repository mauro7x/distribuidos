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
        if not (data.permalink and data.sentiment and data.body):
            logging.debug('Ignoring comment (missing data)')
            return

        try:
            sentiment = float(data.sentiment)
        except Exception:
            logging.debug('Ignoring comment (invalid sentiment)')
            return

        self._send({
            "url": data.permalink,
            "sentiment": sentiment,
            "body": data.body
        })


def main():
    init_log()
    filter = Filter()
    filter.run()


if __name__ == '__main__':
    main()
