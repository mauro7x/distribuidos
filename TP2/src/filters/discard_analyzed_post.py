import logging
from dataclasses import dataclass
from common.filters.custom import Filter
from common.utils import init_log


@dataclass
class Context:
    analyzed_post_ids = set()


def comment_handler(context: Context, send_fn, data):
    logging.debug(f'Handler called with: {data}')
    if data.p_id not in context.analyzed_post_ids:
        send_fn({
            "p_id": data.p_id,
            "body": data.body
        })


def analyzed_post_handler(context: Context, _, data):
    logging.debug(f'Handler called with: {data}')
    context.analyzed_post_ids.add(data.p_id)


def main():
    init_log()
    handlers = {
        "comment": comment_handler,
        "analyzed_post": analyzed_post_handler
    }
    context = Context()
    filter = Filter(handlers, context)
    filter.run()


if __name__ == '__main__':
    main()
