import os
import csv
import logging
import zmq
from multiprocessing import Process
from sys import stdout
from time import sleep, time
from common.csv import CSVParser
from common.utils import init_log

SEND_N = int(os.getenv('SEND_N', '1'))

PRINT_EVERY = 10000


def send_posts():
    context = zmq.Context()
    pusher = context.socket(zmq.PUSH)
    pusher.connect('tcp://purge_post:3000')
    csv_parser = CSVParser()

    start = time()
    last = start
    with open('samples/posts.csv') as csv_src:
        reader = csv.reader(csv_src)
        _ = next(reader)  # skip headers
        sent = 0
        for post in reader:
            if sent % PRINT_EVERY == 0:
                now = time()
                logging.info(
                    f'Posts sent: {sent}'
                    f' (last: {now - last} secs, '
                    f'acum: {now - start} secs)'
                )
                last = now
            if sent == SEND_N:
                break

            post_msg = '0 ' + csv_parser.encode(post)
            pusher.send_string(post_msg)
            sent += 1

    pusher.send_string('EOF')
    logging.info('Finished sending posts')


def send_comments():
    context = zmq.Context()
    pusher = context.socket(zmq.PUSH)
    pusher.connect('tcp://purge_comment:3000')
    csv_parser = CSVParser()

    start = time()
    last = start
    with open('samples/comments.csv') as csv_src:
        reader = csv.reader(csv_src)
        _ = next(reader)  # skip headers
        sent = 0
        for comment in reader:
            if sent % PRINT_EVERY == 0:
                now = time()
                logging.info(
                    f'Comments sent: {sent}'
                    f' (last: {now - last} secs, '
                    f'acum: {now - start} secs)'
                )
                last = now
            if sent == SEND_N:
                break

            comment_msg = '0 ' + csv_parser.encode(comment)
            pusher.send_string(comment_msg)
            sent += 1

    pusher.send_string('EOF')
    logging.info('Finished sending comments')


def main():
    init_log()
    logging.info('Started. Waiting for system...')
    sleep(10)
    logging.info('Starting sending processes...')
    stdout.flush()

    start = time()
    post_sender = Process(target=send_posts)
    comment_sender = Process(target=send_comments)
    post_sender.start()
    comment_sender.start()
    post_sender.join()
    comment_sender.join()

    elapsed = time() - start
    logging.info(f'Finished (elapsed: {elapsed:.2f})')
    stdout.flush()


if __name__ == "__main__":
    main()
