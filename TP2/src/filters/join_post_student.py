import logging
from common.filter import BaseFilter
from common.utils import init_log


class Filter(BaseFilter):
    def __init__(self):
        super().__init__()
        self._handlers = {
            "post": self.__post_handler,
            "student_post": self.__student_post_handler
        }
        self.__waiting_student_related = {}
        self.__waiting_post_data = set()

    def __post_handler(self, data):
        logging.debug(f'Handler called with: {data}')
        p_id = data.p_id
        img_url = data.img_url
        score = float(data.score)

        if p_id in self.__waiting_post_data:
            self._send({
                "p_id": p_id,
                "img_url": img_url,
                "score": score
            })
            self.__waiting_post_data.remove(p_id)
        else:
            self.__waiting_student_related[data.p_id] = (img_url, score)

    def __student_post_handler(self, data):
        logging.debug(f'Handler called with: {data}')
        p_id = data.p_id

        if p_id in self.__waiting_student_related:
            img_url, score = self.__waiting_student_related.pop(p_id)
            self._send({
                "p_id": p_id,
                "img_url": img_url,
                "score": score
            })
            return

        self.__waiting_post_data.add(p_id)


def main():
    init_log()
    filter = Filter()
    filter.run()


if __name__ == '__main__':
    main()
