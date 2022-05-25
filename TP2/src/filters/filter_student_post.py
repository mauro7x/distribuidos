from common.filter import BaseFilter
from common.utils import init_log


STUDENT_RELATED_WORDS = set(
    ['university', 'college', 'student', 'teacher', 'professor'])


class Filter(BaseFilter):
    def __init__(self):
        super().__init__()
        self._handlers = {
            "comment": self.__comment_handler
        }
        self.__student_posts = set()

    def __comment_handler(self, data):
        if data.p_id in self.__student_posts:
            return

        if Filter.__is_student_related(data.body):
            self.__student_posts.add(data.p_id)
            self._send({"p_id": data.p_id})

    # Helpers

    @staticmethod
    def __is_student_related(body: str):
        for word in body.split(' '):
            word = word.lower()
            if word in STUDENT_RELATED_WORDS:
                return True
        return False


def main():
    init_log()
    filter = Filter()
    filter.run()


if __name__ == '__main__':
    main()
