import logging
from common.filter import Filter
from common.utils import init_log


def msg_1_handler(_, send_fn, data):
    logging.info(f'Handler called with: {data}')
    first_name = data.first_name
    last_name = data.last_name

    send_fn({
        'dni': data.dni,
        'fullname': f'{first_name} {last_name}'
    })


def main():
    init_log()
    handlers = {"msg_1": msg_1_handler}
    context = {}
    filter = Filter(handlers, context)
    filter.run()


if __name__ == '__main__':
    main()
