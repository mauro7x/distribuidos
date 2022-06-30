import os
from time import sleep
import signal
import os

_print = print


def print(msg):
    _print(f'<data> {msg}')


def sigterm_handler(*args):
    print('Sigterm handler')
    os._exit(0)


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    while True:
        print('Simulating work...')
        sleep(1)


if __name__ == "__main__":
    main()
