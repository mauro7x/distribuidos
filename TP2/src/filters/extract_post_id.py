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
        p_id = Filter.extract_post_id(data.url)

        self._send({
            "p_id": p_id,
            "sentiment": data.sentiment,
            "body": data.body
        })

    # Helpers

    @staticmethod
    def extract_post_id(url: str):
        # Format: protocol://host/r/meirl/comments/{POST_ID}/meirl/{comment_id}
        # e.g.: https://old.reddit.com/r/meirl/comments/tswh3j/meirl/i2x2j0g/
        # Splitting by '/', 7th group is our ID
        return url.split('/')[6]

    # Alternative regex method:
    # import re
    # REGEX = r'comments/([^/]*)'
    #
    # def extract_post_id(url: str):
    #     return re.findall(REGEX, url)[0]


def main():
    init_log()
    filter = Filter()
    filter.run()


if __name__ == '__main__':
    main()
