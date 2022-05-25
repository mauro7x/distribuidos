import logging
from common.filter import BaseFilter
from common.utils import init_log


class Filter(BaseFilter):
    def __init__(self):
        super().__init__()
        self._handlers = {
            "post_url": self.__post_url_handler,
            "post_sentiment": self.__post_sentiment_handler
        }
        self.__posts = {}

    def __post_url_handler(self, data):
        logging.debug(f'Handler called with: {data}')
        _, avg, count = self.__posts.get(data.p_id, (None, None, 0))
        self.__posts[data.p_id] = (data.img_url, avg, count)

    def __post_sentiment_handler(self, data):
        logging.debug(f'Handler called with: {data}')
        sentiment = float(data.sentiment)
        url, avg, count = self.__posts.get(data.p_id, (None, None, 0))
        if avg is None:
            self.__posts[data.p_id] = (url, sentiment, 1)
            return

        count += 1
        new_avg = (avg * (1 - (1 / count)) +
                   (sentiment / count))
        self.__posts[data.p_id] = (url, new_avg, count)

    def _eof_handler(self):
        logging.debug('EOF handler called')
        valid_posts = self.__filter_valid_posts()
        if not valid_posts:
            logging.warning('Final: no valid posts')
            return

        p_id, post = Filter.__get_max_avg(valid_posts)
        url, avg, _ = post
        self._send({
            "p_id": p_id,
            "img_url": url,
            "avg_sentiment": avg
        })

    # Helpers

    def __filter_valid_posts(self):
        result = {}
        for p_id, post in self.__posts.items():
            url, avg, _ = post
            if url is None or avg is None:
                continue
            result[p_id] = post

        return result

    @staticmethod
    def __get_max_avg(valid_posts):
        iterator = iter(valid_posts.items())
        result = next(iterator)

        for p_id, post in iterator:
            _, avg, _ = post
            if avg > result[1][1]:
                result = (p_id, post)

        return result


def main():
    init_log()
    filter = Filter()
    filter.run()


if __name__ == '__main__':
    main()
