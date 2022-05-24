import logging
from collections import defaultdict
from dataclasses import dataclass
from common.filter import Filter
from common.types import Average
from common.utils import init_log


class Post:
    def __init__(self):
        self.img_url: str = None
        self.aggregator = Average()


@dataclass
class Context:
    posts = defaultdict(Post)


def filter_valid_posts(posts: defaultdict[str, Post]):
    result = {}
    for p_id, post in posts.items():
        if post.img_url is None or post.aggregator.get() is None:
            continue
        result[p_id] = post

    return result


def get_max_avg(valid_posts: defaultdict[str, Post]):
    iterator = iter(valid_posts.items())
    result = next(iterator)

    for p_id, post in iterator:
        avg = post.aggregator.get()
        if avg > result[1].aggregator.get():
            result = (p_id, post)

    return result


def post_url_handler(context: Context, _, data):
    logging.debug(f'Handler called with: {data}')
    post = context.posts[data.p_id]
    post.img_url = data.img_url


def post_sentiment_handler(context: Context, _, data):
    logging.debug(f'Handler called with: {data}')
    sentiment = float(data.sentiment)
    post = context.posts[data.p_id]
    post.aggregator.add(sentiment)


def eof_handler(context: Context, send_fn):
    logging.debug('EOF handler called')

    valid_posts = filter_valid_posts(context.posts)
    if not valid_posts:
        logging.warning('Final: no valid posts')
        return

    p_id, post = get_max_avg(valid_posts)
    send_fn({
        "p_id": p_id,
        "img_url": post.img_url,
        "avg_sentiment": post.aggregator.get()
    })


def main():
    init_log()
    handlers = {
        "post_url": post_url_handler,
        "post_sentiment": post_sentiment_handler
    }
    context = Context()
    filter = Filter(handlers, context)
    filter.set_eof_handler(eof_handler)
    filter.run()


if __name__ == '__main__':
    main()
