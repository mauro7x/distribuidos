import logging
from common.filter import Filter
from common.utils import init_log


def msg_1_handler(_, send_fn, data):
    logging.info(f'Handler called with: {data}')
    age = int(data.age)

    send_fn({
        'dni': data.dni,
        'age_in_months': age * 12
    })


def main():
    init_log()
    handlers = {"msg_1": msg_1_handler}
    context = {}
    filter = Filter(handlers, context)
    filter.run()


if __name__ == '__main__':
    main()
