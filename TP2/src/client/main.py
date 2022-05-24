
import logging
from multiprocessing import Process
from time import sleep, time
from common.utils import init_log

# Processes
from comment_ingestion import run as comment_ingestion_runner
from post_ingestion import run as post_ingestion_runner
from sink import run as sink_runner


def main():
    init_log()
    logging.info('=== Started ===')

    logging.debug('Spawning processes...')
    post_ingestion = Process(target=post_ingestion_runner)
    comment_ingestion = Process(target=comment_ingestion_runner)
    sink = Process(target=sink_runner)

    logging.debug('Starting sink...')
    sink.start()

    logging.debug('Waiting for start signal...')
    # TODO: Replace with signal
    sleep(3)

    start = time()

    logging.debug('Starting ingestors...')
    post_ingestion.start()
    comment_ingestion.start()

    logging.debug('Joining processes...')
    post_ingestion.join()
    comment_ingestion.join()
    sink.join()

    elapsed = time() - start
    logging.info(f'=== Finished === (elapsed: {elapsed:.2f} secs)')


if __name__ == "__main__":
    main()
