from common.filter import Filter
from common.utils import init_log
from time import sleep

# Handlers


def handle_msg_1(context, send, data):
    print('received msg1:', data)
    dni, first_name, last_name = data
    context['names'][dni] = (first_name, last_name)

    if dni in context['ages']:
        age = context['ages'][dni]
        send({
            "dni": dni,
            "first_name": first_name,
            "age": age
        })


def handle_msg_2(context, send, data):
    print('received msg2:', data)
    dni, age = data
    context['ages'][dni] = age

    if dni in context['names']:
        first_name, _ = context['names'][dni]
        send({
            "dni": dni,
            "first_name": first_name,
            "age": age
        })


# Main execution


def main():
    init_log('debug')

    handlers = {
        "msg_1": handle_msg_1,
        "msg_2": handle_msg_2
    }
    context = {
        "names": {},
        "ages": {}
    }
    filter = Filter(handlers, context)
    sleep(1)
    filter.run()


if __name__ == "__main__":
    main()
