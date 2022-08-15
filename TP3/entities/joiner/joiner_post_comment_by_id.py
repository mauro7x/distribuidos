import json
import logging
import os
import time

from common.middleware.middleware import Middleware
from common.constants import FINISH_PROCESSING_TYPE, COMMENT_WITH_POST_INFO_TYPE
from pika.exceptions import ChannelClosed

class Entity:
    def __init__(self, base_config, pipeline_config):
        broker_config = base_config["broker_config"]
        entity_name = base_config["entity_name"]
        entity_config = pipeline_config[entity_name]
        self.entity_name = entity_name

        self._recv_posts_queue_config = pipeline_config["queues"][entity_config["recv_posts_queue"]]
        self._recv_comments_queue_config = pipeline_config[
            "queues"][entity_config["recv_comments_queue"]]

        self._send_exchanges = entity_config["send_exchanges"]

        self.entity_sub_id = os.environ["ENTITY_SUB_ID"]

        self._middleware = Middleware(broker_config, pipeline_config, f"joiner_{self.entity_sub_id}", self.get_backupable_state)
        self.keep_running = True

        self.__reset_state()
        self.__recover_backup_state()
    
    def __reset_state(self):
        # Initialize post consuming
        self._post_map = {}
        self._start_time = time.time()
        self._consuming_posts = True
        self._n_joins = 0
        self._start_consuming_comments_time = None

    def __post_stream_end_callback(self):
        self._consuming_posts = False

        self._start_consuming_comments_time = time.time()
        logging.info("Finished consuming posts: total_posts: {} time_elapsed: {} mins".format(
                    len(self._post_map), (self._start_consuming_comments_time - self._start_time) / 60))

        self._middleware.stop_consuming()

    def __comment_stream_end_callback(self):
        logging.info("Finished joining comments with posts: total_joins: {} time_elapsed: {} mins".format(
                    self._n_joins, (time.time() - self._start_consuming_comments_time) / 60))

        self._middleware.send_termination(self._send_exchanges, {
                                                "type": FINISH_PROCESSING_TYPE})

        self.__reset_state()
        self._middleware.stop_consuming()

    def run(self):
        while self.keep_running:
            try:
                if self._consuming_posts:
                    self._middleware.start_consuming(
                        self._recv_posts_queue_config, self.process_post, self.__post_stream_end_callback, self.entity_sub_id)
                
                if not self._consuming_posts:
                    self._middleware.start_consuming(
                        self._recv_comments_queue_config, self.join_comment_with_post, self.__comment_stream_end_callback, self.entity_sub_id)

            except ChannelClosed:
                break

    def stop(self):
        self.keep_running = False
        self._middleware.stop_consuming()
        self._middleware.close()

    def process_post(self, post):
        post_id = post["id"]
        del post["id"]
        del post["type"]
        self._post_map[post_id] = post

        # with open(f".data_backup/post_map_joiner_{os.environ['ENTITY_SUB_ID']}.json",'w') as f:
        #     f.write(json.dumps(self._post_map))
        #     f.flush()

    def join_comment_with_post(self, comment):
        self._n_joins += 1
        del comment["type"]

        post_data = self._post_map.get(comment["post_id"], None)
        if not post_data:
            # logging.info("dropping comment with post_id: {} because it does not have post data associated (it was filtered if existent)".format(
            #     comment["post_id"]))
            return

        join_result = {**comment, **post_data}
        join_result["type"] = COMMENT_WITH_POST_INFO_TYPE

        # logging.debug("Sending joined post/comment: {}".format(join_result))

        self._middleware.send(self._send_exchanges, join_result)

    def get_backupable_state(self):
        return {
            "post_map": self._post_map,
            "start_time": self._start_time,
            "n_joins": self._n_joins,
            "consuming_posts": self._consuming_posts,
            "start_consuming_comments_time": self._start_consuming_comments_time
        }
    
    def __recover_backup_state(self):
        backup_state = self._middleware.recover_user_backup_state()
        if not backup_state:
            logging.info("Backup state not found. Starting from scratch.")
            return

        try:
            self._post_map = backup_state["post_map"]
            self._start_time = backup_state["start_time"]
            self._n_joins = backup_state["n_joins"]
            self._consuming_posts = backup_state["consuming_posts"]
            self._start_consuming_comments_time = backup_state["start_consuming_comments_time"]
        except Exception as e:
            logging.error(f"Error recovering backup state: {e}")
            self.__reset_state()
            return
