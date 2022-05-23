import csv
from multiprocessing import Process
from sys import stdout
import zmq
from time import sleep


SEND_N = 1


def send_posts():
    context = zmq.Context()
    pusher = context.socket(zmq.PUSH)
    pusher.connect('tcp://purge_post:3000')

    with open('samples/posts.csv') as csv_src:
        reader = csv.reader(csv_src)
        sent = 0
        for post in reader:
            if sent == SEND_N:
                break

            post_str = '0 ' + ','.join(post)
            pusher.send_string(post_str)
            print('Sent:', post_str)
            sent += 1

    print('Finished sending posts')


def send_comments():
    context = zmq.Context()
    pusher = context.socket(zmq.PUSH)
    pusher.connect('tcp://purge_comment:3000')

    with open('samples/comments.csv') as csv_src:
        reader = csv.reader(csv_src)
        sent = 0
        for comment in reader:
            if sent == SEND_N:
                break

            comment_str = '0 ' + ','.join(comment)
            pusher.send_string(comment_str)
            print('Sent:', comment_str)
            sent += 1

    print('Finished sending comments')


def main():
    print('Started. Waiting for system...')
    sleep(5)
    print('Starting sending processes...')
    stdout.flush()

    post_sender = Process(target=send_posts)
    comment_sender = Process(target=send_comments)
    post_sender.start()
    comment_sender.start()
    post_sender.join()
    comment_sender.join()

    print('Finished')
    stdout.flush()


if __name__ == "__main__":
    main()
