
import logging
from multiprocessing import Process
from time import sleep, time

import constants as const
from common.utils import init_log, read_json

# Processes
from ingestion import run as ingestion_runner, IngestionConfig
from sink import run as sink_runner, SinkConfig


class Client:
    def __init__(self):
        logging.debug('Initializing...')
        self.__spawn_processes()
        self.__start_sink()
        self.__wait_server_readiness()
        logging.debug('Client initialized and ready')

    def run(self):
        self.__start_ingestion()
        self.__join()

    # Private

    def __spawn_processes(self):
        logging.debug('Spawning processes...')
        try:
            self.__spawn_ingestion()
            self.__spawn_sink()
        except Exception:
            raise Exception('Could not spawn processes: invalid config')

    def __spawn_ingestion(self):
        self.__ingestion_processes = []
        config = read_json(const.INGESTION_CONFIG_FILEPATH)
        common_config = read_json(const.COMMON_CONFIG_FILEPATH)

        # Posts ingestion
        posts_config = config['posts']
        post_ingestion = Process(
            target=ingestion_runner,
            args=(IngestionConfig(
                'Post Ingestion',
                posts_config['src_filepath'],
                posts_config['host'],
                int(common_config['port']),
                common_config['protocol'],
                int(common_config['batch_size']),
                int(posts_config['print_info_every_msgs']),
                bool(posts_config['skip_headers']),
                int(posts_config['limit']),
                int(posts_config['msg_idx'])
            ),)
        )
        self.__ingestion_processes.append(post_ingestion)

        # Comments ingestion
        comments_config = config['comments']
        comment_ingestion = Process(
            target=ingestion_runner,
            args=(IngestionConfig(
                'Comment Ingestion',
                comments_config['src_filepath'],
                comments_config['host'],
                int(common_config['port']),
                common_config['protocol'],
                int(common_config['batch_size']),
                int(comments_config['print_info_every_msgs']),
                bool(comments_config['skip_headers']),
                int(comments_config['limit']),
                int(comments_config['msg_idx'])
            ),)
        )

        self.__ingestion_processes.append(comment_ingestion)

    def __spawn_sink(self):
        config = read_json(const.SINK_CONFIG_FILEPATH)
        common_config = read_json(const.COMMON_CONFIG_FILEPATH)

        sink = Process(
            target=sink_runner,
            args=(SinkConfig(
                'Sink',
                int(common_config['port']),
                common_config['protocol'],
                int(config['sources'])
            ),)
        )
        self.__sink_processes = [sink]

    def __start_ingestion(self):
        logging.debug('Starting ingestion...')
        for ingestion in self.__ingestion_processes:
            ingestion.start()

    def __start_sink(self):
        logging.debug('Starting sink...')
        for sink in self.__sink_processes:
            sink.start()

    def __wait_server_readiness(self):
        logging.debug('Waiting for server readiness...')
        # TODO: Replace with signal
        sleep(5)

    def __join(self):
        processes = [*self.__ingestion_processes, *self.__sink_processes]
        for process in processes:
            process.join()


def main():
    init_log()
    client = Client()
    start = time()
    client.run()
    elapsed = time() - start
    logging.info(f'Finished (elapsed: {elapsed:.2f} secs)')


if __name__ == "__main__":
    main()
