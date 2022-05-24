import logging
from dataclasses import dataclass
from common.filters.custom import Filter
from common.utils import init_log


STUDENT_RELATED_WORDS = set(
    ['university', 'college', 'student', 'teacher', 'professor'])


@dataclass
class Context:
    student_posts = set()


def is_student_related(body: str):
    for word in body.split(' '):
        word = word.lower()
        if word in STUDENT_RELATED_WORDS:
            return True
    return False


def comment_handler(context: Context, send_fn, data):
    logging.debug(f'Handler called with: {data}')

    if data.p_id in context.student_posts:
        return

    if is_student_related(data.body):
        context.student_posts.add(data.p_id)
        send_fn({"p_id": data.p_id})


def main():
    init_log()
    handlers = {"comment": comment_handler}
    context = Context()
    filter = Filter(handlers, context)
    filter.run()


if __name__ == '__main__':
    main()
