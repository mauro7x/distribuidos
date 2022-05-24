import logging
from dataclasses import dataclass
from typing import NamedTuple
from common.filters.custom import Filter
from common.utils import init_log


class Post(NamedTuple):
    img_url: str
    score: float


@dataclass
class Context:
    waiting_avg_score = []
    avg_score: float = None


def post_handler(context: Context, send_fn, data):
    logging.debug(f'Handler called with: {data}')
    img_url = data.img_url
    score = float(data.score)

    if not context.avg_score:
        post = Post(img_url, score)
        context.waiting_avg_score.append(post)
        return

    send_fn({"img_url": img_url})

    # Temp:
    logging.warning(f'Student meme: {img_url}')


def avg_score_handler(context: Context, send_fn, data):
    logging.debug(f'Handler called with: {data}')
    avg_score = float(data.avg_score)
    context.avg_score = avg_score

    for post in context.waiting_avg_score:
        if post.score > avg_score:
            send_fn({"img_url": post.img_url})


def main():
    init_log()
    handlers = {
        "post": post_handler,
        "avg_score": avg_score_handler
    }
    context = Context()
    filter = Filter(handlers, context)
    filter.run()


if __name__ == '__main__':
    main()
