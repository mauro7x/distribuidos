import logging
from common.filters.custom import Filter
from common.utils import init_log

# Regex method:
# import re
# REGEX = r'comments/([^/]*)'
#
# def extract_post_id(url):
#     return re.findall(REGEX, url)[0]


# Split method:
def extract_post_id(url):
    # Format: protocol://host/r/meirl/comments/{POST_ID}/meirl/{comment_id}
    # e.g.: https://old.reddit.com/r/meirl/comments/tswh3j/meirl/i2x2j0g/
    # Splitting by '/', 7th group is our ID
    return url.split('/')[6]


def comment_handler(_, send_fn, data):
    logging.info(f'Handler called with: {data}')
    p_id = extract_post_id(data.url)

    send_fn({
        "p_id": p_id,
        "sentiment": data.sentiment,
        "body": data.body
    })


def main():
    init_log()
    handlers = {"comment": comment_handler}
    filter = Filter(handlers)
    filter.run()


if __name__ == '__main__':
    main()
