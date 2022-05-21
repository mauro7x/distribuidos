from sys import stdout
import zmq


def main():
    print('Started')
    context = zmq.Context()
    puller = context.socket(zmq.PULL)
    puller.bind('tcp://*:3000')

    while True:
        data = puller.recv_string()
        print('Received:', data)
        stdout.flush()


if __name__ == "__main__":
    main()
