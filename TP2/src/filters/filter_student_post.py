import logging
from common.filters.custom import Filter
from common.utils import init_log

STUDENT_RELATED_WORDS = set(
    ['university', 'college', 'student', 'teacher', 'professor'])


def is_student_related(body: str):
    for word in body.split(' '):
        word = word.lower()
        if word in STUDENT_RELATED_WORDS:
            return True
    return False


def comment_handler(_, send_fn, data):
    logging.debug(f'Handler called with: {data}')

    if is_student_related(data.body):
        send_fn({"p_id": data.p_id})


def main():
    init_log()
    handlers = {"comment": comment_handler}
    filter = Filter(handlers)
    filter.run()


if __name__ == '__main__':
    main()
