import logging
from common.filter import Filter
from common.utils import init_log


def msg_1_handler(context, _, data):
    logging.info(f'Handler called with: {data}')
    dni = data.dni
    fullname = data.fullname
    context['names'][dni] = fullname

    if dni in context['ages']:
        age_in_months = context['ages'][dni]
        logging.info(f'Result: ({dni}, {fullname}, {age_in_months})')


def msg_2_handler(context, _, data):
    logging.info(f'Handler called with: {data}')
    dni = data.dni
    age_in_months = data.age_in_months
    context['ages'][dni] = age_in_months

    if dni in context['names']:
        fullname = context['names'][dni]
        logging.info(f'Result: ({dni}, {fullname}, {age_in_months})')


def main():
    init_log()
    handlers = {"msg_1": msg_1_handler, "msg_2": msg_2_handler}
    context = {
        'names': {},
        'ages': {}
    }
    filter = Filter(handlers, context)
    filter.run()


if __name__ == '__main__':
    main()
