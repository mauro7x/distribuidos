import logging
import requests
import socket
import time
import common.cs_protocol

from common.middleware.middleware import Middleware
from common.constants import FINISH_PROCESSING_TYPE, POST_WITH_MAX_AVG_SENTIMENT_TYPE, BATCH_TYPE
from mimetypes import guess_extension

POSTS_FILE = '/posts.csv'
COMMENTS_FILE = '/comments.csv'


class Entity:
    def __init__(self, base_config, pipeline_config):
        server_config = base_config["server_config"]
        broker_config = base_config["broker_config"]
        entity_name = base_config["entity_name"]
        entity_config = pipeline_config[entity_name]

        self.entity_name = entity_name

        self._send_posts_exchanges = pipeline_config[self.entity_name]["send_posts_exchanges"]
        self._send_comments_exchanges = pipeline_config[self.entity_name]["send_comments_exchanges"]

        self._recv_queue_config = pipeline_config["queues"][entity_config["recv_queue"]]

        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', server_config["port"]))
        self._server_socket.listen(server_config["listen_backlog"])

        logging.info("Listening on {}".format(server_config["port"]))

        self._middleware = Middleware(broker_config, pipeline_config, "ingestor", self.get_backupable_state, recover_backup = False)

        self._ingesting_posts = False
        self._ingesting_comments = False

        self.keep_running = True

    def consume_results(self, result):
        if result['type'] == POST_WITH_MAX_AVG_SENTIMENT_TYPE:
            logging.info(
                "Received result post_with_max_avg_sentiment_type: {}".format(result))
            self.__download_and_send_post_with_max_avg_sentiment(result)
            return

        common.cs_protocol.send(self._client_sock, result)
    
    def __recover_backup_state(self):
        backup_state = self._middleware.recover_user_backup_state()
        if not backup_state:
            logging.info("Backup state not found. Starting from scratch.")
            return

        return backup_state

    def get_backupable_state(self):
        return {
            "ingesting_posts": self._ingesting_posts,
            "ingesting_comments": self._ingesting_comments,
        }

    def __force_flush(self):
        backup_state = self.__recover_backup_state()
        if not backup_state or "ingesting_posts" not in backup_state or "ingesting_comments" not in backup_state: 
            return

        termination_msg = {
            "type": FINISH_PROCESSING_TYPE}

        if backup_state["ingesting_posts"]:
            self._middleware.send_termination(
                self._send_posts_exchanges, termination_msg, skip_deduplication=True)
            self._middleware.send_termination(
                self._send_comments_exchanges, termination_msg, skip_deduplication=True)

        if backup_state["ingesting_comments"]:
            self._middleware.send_termination(
                self._send_comments_exchanges, termination_msg, skip_deduplication=True)

        if backup_state["ingesting_posts"] or backup_state["ingesting_comments"]: 
            # Receive and discard partial results
            self._middleware.start_consuming(
                self._recv_queue_config, lambda _: None, self._middleware.stop_consuming)

    def send_termination(self):
        termination_msg = {
            "type": FINISH_PROCESSING_TYPE}

        common.cs_protocol.send(self._client_sock, termination_msg)

        self._client_sock.close()
        self._middleware.stop_consuming()

    def stop(self):
        self.keep_running = False
        self.send_termination()
        self._middleware.close()
        self._server_socket.close()

    def __ingest(self, exchanges):
        while True:
            batch = common.cs_protocol.recv(self._client_sock)
            if batch["type"] == FINISH_PROCESSING_TYPE:
                break
            
            if batch["type"] != BATCH_TYPE:
                logging.warn(f"Received unexpected message type: {batch['type']}")
                continue

            for element in batch["data"]:
                self._middleware.send(exchanges, element)

        self._middleware.send_termination(
            exchanges, {"type": FINISH_PROCESSING_TYPE})

    def run(self):
        while self.keep_running:

            logging.info("Cleaning up pipeline")
            self.__force_flush()
            logging.info("Cleanup done")

            client_sock = self.__accept_new_connection()
            if not client_sock:
                continue

            self._client_sock = client_sock

            self._start_time = time.time()

            self._ingesting_posts = True
            self._middleware.force_backup()
            self.__ingest(self._send_posts_exchanges)
            self._ingesting_posts = False
            self._finish_ingesting_posts_time = time.time()

            logging.info("Finished ingesting posts: time_elapsed: {} mins".format(
                (self._finish_ingesting_posts_time - self._start_time) / 60))

            self._ingesting_comments = True
            self._middleware.force_backup()
            self.__ingest(self._send_comments_exchanges)
            self._ingesting_comments = False
            self._finish_ingesting_comments_time = time.time()

            self._middleware.force_backup()
            logging.info("Finished ingesting comments: time_elapsed: {} mins".format(
                (self._finish_ingesting_comments_time - self._finish_ingesting_posts_time) / 60))

            self._middleware.start_consuming(
                self._recv_queue_config, self.consume_results, self.send_termination)

    def __accept_new_connection(self):
        logging.info("Proceed to accept new connections")
        try:
            c, addr = self._server_socket.accept()
        except:
            logging.info(
                "Stop accepting clients, socket not available anymore")
            return None
        logging.info('Got connection from {}'.format(addr))
        return c

    def __download_and_send_post_with_max_avg_sentiment(self, result):
        url = result["url"]

        try:
            r = requests.get(url, allow_redirects=True)

            if r.status_code != 200:
                logging.error(
                    "Could not download img of post_with_max_avg_sentiment: {}".format(
                        result))
                common.cs_protocol.send(self._client_sock, result)
                return

            file_ext = guess_extension(
                r.headers['content-type'].partition(';')[0].strip())

            if not file_ext:
                file_ext = ".unknown"

            result["ext"] = file_ext
            result["file_length"] = len(r.content)

            logging.info("Image downloaded successfully")

            common.cs_protocol.send(self._client_sock, result)
            common.cs_protocol.send_img(self._client_sock, r.content)
        except:
            logging.error(
                "Could not download img of post_with_max_avg_sentiment: {}".format(result))
            common.cs_protocol.send(self._client_sock, result)
            return
