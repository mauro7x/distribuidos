from sys import stdout
import zmq
from time import sleep


def main():
    print('Started')
    context = zmq.Context()
    pusher = context.socket(zmq.PUSH)
    pusher.connect('tcp://filter:3000')

    sleep(2)

    data = [
        '1 123,22',
        '0 321,juan,perez',
        '1 321,45',
        '0 123,mauro,parafati'
    ]
    for line in data:
        pusher.send_string(line)
        print('Sent:', line)

    print('Finished')
    stdout.flush()


if __name__ == "__main__":
    main()
