import signal
import zmq

PORT = 3000


_print = print


context = zmq.Context()


def print(msg):
    _print(f'<control> {msg}')


def sigterm_handler(*_):
    print('Sigterm handler')
    context.destroy(0)
    exit(0)


def main():
    print('Hello World!')
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    socket = context.socket(zmq.REP)
    socket.bind(f'tcp://*:{PORT}')

    while True:
        try:
            socket.recv()
            socket.send(b'')
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
