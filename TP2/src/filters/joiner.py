import logging
from common.filter import Filter
from common.utils import init_log


def example_handler(context, send_fn, data):
    name = context['name']
    logging.info(f'[{name}] Handler called with: {data}')


def main():
    init_log('debug')

    handlers = {}
    context = {'name': 'Joiner'}
    filter = Filter(handlers, context)
    filter.run()


if __name__ == '__main__':
    main()
