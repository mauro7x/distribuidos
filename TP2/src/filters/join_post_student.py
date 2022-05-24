import logging
from collections import defaultdict
from dataclasses import dataclass
from common.filters.custom import Filter
from common.utils import init_log


class Post:
    def __init__(self):
        self.img_url: str = None
        self.score: float = None


@dataclass
class Context:
    waiting_student_related = defaultdict(Post)
    waiting_post_data = set()


def post_handler(context: Context, send_fn, data):
    logging.debug(f'Handler called with: {data}')
    p_id = data.p_id
    img_url = data.img_url
    score = float(data.score)

    if p_id in context.waiting_post_data:
        send_fn({
            "p_id": p_id,
            "img_url": img_url,
            "score": score
        })
        context.waiting_post_data.remove(p_id)
        return

    post = context.waiting_student_related[data.p_id]
    post.img_url = img_url
    post.score = score


def student_post_handler(context: Context, send_fn, data):
    logging.debug(f'Handler called with: {data}')
    p_id = data.p_id

    if p_id in context.waiting_student_related:
        post = context.waiting_student_related.pop(p_id)
        send_fn({
            "p_id": p_id,
            "img_url": post.img_url,
            "score": post.score
        })
        return

    context.waiting_post_data.add(p_id)


def main():
    init_log()
    handlers = {
        "post": post_handler,
        "student_post": student_post_handler
    }
    context = Context()
    filter = Filter(handlers, context)
    filter.run()


if __name__ == '__main__':
    main()
