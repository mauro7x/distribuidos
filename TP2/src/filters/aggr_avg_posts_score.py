from common.filter import BaseFilter
from common.utils import init_log


class Filter(BaseFilter):
    def __init__(self):
        super().__init__()
        self._handlers = {
            "score": self.__score_handler
        }
        self.__avg = None
        self.__count = 0

    def __score_handler(self, data):
        score = int(data.score)
        self.__count += 1
        if self.__avg is None:
            self.__avg = score
            return

        self.__avg = (self.__avg * (1 - (1 / self.__count)) +
                      (score / self.__count))

    def _eof_handler(self):
        self._send({"avg_score": self.__avg})


def main():
    init_log()
    filter = Filter()
    filter.run()


if __name__ == '__main__':
    main()
