from sys import stdout
import zmq
from time import sleep


def main():
    print('Started')
    context = zmq.Context()
    pusher = context.socket(zmq.PUSH)
    pusher.connect('tcp://ingestion:3000')

    # dni,first_name,last_name,age,extra,drop_this,thrash
    data = [
        '0 123,mauro,parafati,23,jeje,jojo,juju',
        '0 124,emma,hansen,9,ffdf,jojo,keke',
        '0 125,aaron,hansen,14,sdfdsg,lfdg,isis',
        '0 126,paula,parafati,41,3454353,jojo,www'
    ]

    sleep(5)

    print('Starting to send data')
    stdout.flush()

    for line in data:
        pusher.send_string(line)
        print('Sent:', line)

    print('Finished')
    stdout.flush()


if __name__ == "__main__":
    main()
