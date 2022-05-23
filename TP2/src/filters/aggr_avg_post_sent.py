import logging
from collections import defaultdict
from dataclasses import dataclass
from common.filters.custom import Filter
from common.types import Average
from common.utils import init_log


@dataclass
class Context:
    avg_post_sentiments = defaultdict(Average)


def get_max_avg(avg_post_sentiments: defaultdict[str, Average]):
    iterator = iter(avg_post_sentiments.items())
    p_id, aggr = next(iterator)
    result = p_id, aggr.get()

    for p_id, aggr in iterator:
        avg = aggr.get()
        if avg > result[1]:
            result = (p_id, avg)

    return result


def sentiment_handler(context: Context, _, data):
    logging.debug(f'Handler called with: {data}')
    p_id = data.p_id
    sentiment = float(data.sentiment)
    context.avg_post_sentiments[p_id].add(sentiment)


def eof_handler(context: Context, send_fn):
    logging.debug('EOF handler called')
    p_id, avg = get_max_avg(context.avg_post_sentiments)
    send_fn({"p_id": p_id, "avg_sentiment": avg})

    # Temp:
    print('Final:')
    print('- Post ID:', p_id)
    print('- AVG:', avg)


def main():
    init_log()
    handlers = {"sentiment": sentiment_handler}
    context = Context()
    filter = Filter(handlers, context)
    filter.set_eof_handler(eof_handler)
    filter.run()


if __name__ == '__main__':
    main()
