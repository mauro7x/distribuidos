from common.filter import BaseFilter
from common.utils import init_log


class Filter(BaseFilter):
    def __init__(self):
        super().__init__()
        self._handlers = {
            "post": self.__post_handler,
            "avg_score": self.__avg_score_handler
        }
        self.__waiting_avg_score = []
        self.__avg_score: float = None

    def __post_handler(self, data):
        img_url = data.img_url
        score = float(data.score)

        if not self.__avg_score:
            post = (img_url, score)
            self.__waiting_avg_score.append(post)
            return

        self._send({"img_url": img_url})

    def __avg_score_handler(self, data):
        avg_score = float(data.avg_score)
        self.__avg_score = avg_score

        for post in self.__waiting_avg_score:
            url, score = post
            if score > avg_score:
                self._send({"img_url": url})


def main():
    init_log()
    filter = Filter()
    filter.run()


if __name__ == '__main__':
    main()
