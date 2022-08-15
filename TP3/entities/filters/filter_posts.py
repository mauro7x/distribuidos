import logging
import os
import time
from common.basic_filter import BasicFilter
from common.constants import FINISH_PROCESSING_TYPE, POST_TYPE

class Entity(BasicFilter):
    def __init__(self, base_config, pipeline_config):
        BasicFilter.__init__(self, base_config, pipeline_config,
                              "filter_posts", os.environ["ENTITY_SUB_ID"])
        self._reset_state()
        self._recover_backup_state()


    def _reset_state(self):
        self._n_dropped_posts = 0
        self._n_processed_posts = 0

    def stream_end_callback(self):
        logging.info("Finished: n_processed_posts: {} n_dropped_posts: {} time_elapsed: {} mins".format(
            self._n_processed_posts, self._n_dropped_posts, (time.time() - self._start_time) / 60))

        self._middleware.send_termination(
            self._send_exchanges, {"type": FINISH_PROCESSING_TYPE})

        self._reset_state()

    def stop(self):
        self._middleware.stop_consuming()
        self._middleware.close()

    def get_backupable_state(self):
        return {
            'n_dropped_posts': self._n_dropped_posts,
            'n_processed_posts': self._n_processed_posts
        }

    def callback(self, payload):
        # logging.debug("Received post: {}".format(payload))
        self._n_processed_posts += 1

        parsed_post = {"type": POST_TYPE}
        keys_to_extract = ['id', 'url', 'score']

        for k in keys_to_extract:
            parsed_post[k] = payload.get(k)

        try:
            int(parsed_post['score'])
        except:
            # logging.debug(
            #     "Dropping invalid post: score is not numeric: {}".format(parsed_post['score']))
            self._n_dropped_posts += 1
            return

        # logging.debug("Sending parsed post: {}".format(parsed_post))
        self._middleware.send(self._send_exchanges, parsed_post)
    
    def _recover_backup_state_impl(self,backup_state):
        self._n_dropped_posts = backup_state["n_dropped_posts"]
        self._n_processed_posts = backup_state["n_processed_posts"]
