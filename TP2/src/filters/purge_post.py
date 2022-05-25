import logging
from common.filter import BaseFilter
from common.utils import init_log


class Filter(BaseFilter):
    def __init__(self):
        super().__init__()
        self._handlers = {
            "post": self.__post_handler
        }

    def __post_handler(self, data):
        if not (data.id and data.url and data.score):
            logging.debug('Ignoring post (missing data)')
            return

        try:
            score = int(data.score)
        except Exception:
            logging.debug('Ignoring post (invalid score)')
            return

        self._send({
            "p_id": data.id,
            "img_url": data.url,
            "score": score
        })


def main():
    init_log()
    filter = Filter()
    filter.run()


if __name__ == '__main__':
    main()
