import logging
from common.filter import BaseFilter
from common.utils import init_log


VALID_IMG_EXTENSIONS = set(['jpg', 'jpeg', 'png'])


class Filter(BaseFilter):
    def __init__(self):
        super().__init__()
        self._handlers = {
            "post": self.__post_handler
        }

    def __post_handler(self, data):
        if not Filter.__is_img(data.img_url):
            logging.debug(
                f'Ignoring post (missing image in URL): {data.img_url}')
            return

        self._send({
            "p_id": data.p_id,
            "img_url": data.img_url,
            "score": data.score
        })

    # Helpers

    @staticmethod
    def __is_img(url: str):
        try:
            _, extension = url.rsplit('.', 1)
            return extension.lower() in VALID_IMG_EXTENSIONS
        except Exception:
            return False


def main():
    init_log()
    filter = Filter()
    filter.run()


if __name__ == '__main__':
    main()
