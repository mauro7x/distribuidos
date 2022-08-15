import logging
import os
import re

from common.middleware.middleware import Middleware
from common.constants import FINISH_PROCESSING_TYPE, STUDENT_LIKED_POST_WITH_SCORE_AVG_HIGHER_THAN_MEAN_TYPE
from pika.exceptions import ChannelClosed

class Entity:
    def __init__(self, base_config, pipeline_config):
        broker_config = base_config["broker_config"]
        entity_name = base_config["entity_name"]
        entity_config = pipeline_config[entity_name]
        self.entity_name = entity_name

        self._recv_post_avg_score_queue_config = pipeline_config[
            "queues"][entity_config["recv_post_avg_score_queue"]]
        self._recv_joined_post_comments_queue_config = pipeline_config[
            "queues"][entity_config["recv_joined_post_comments_queue"]]

        self._send_exchanges = entity_config["send_exchanges"]

        self.entity_sub_id = os.environ["ENTITY_SUB_ID"]

        self._middleware = Middleware(broker_config, pipeline_config, f"filter_student_liked_posts_{self.entity_sub_id}", self.get_backupable_state)

        self._student_regexp = re.compile(
            "(?:university|college|student|teacher|professor)", flags=re.IGNORECASE)

        self.keep_running = True
        self.__reset_state()
        self.__recover_backup_state()

    def __reset_state(self):
        self._post_avg_score = None
        self._consuming_post_avg_score = True
        self._posts_already_sent = set()

    def run(self):
        while self.keep_running:
            try:
                if self._consuming_post_avg_score:
                    self._middleware.start_consuming(
                        self._recv_post_avg_score_queue_config, self.process_post_avg_score, self.__post_avg_score_stream_end_callback, self.entity_sub_id)

                if not self._consuming_post_avg_score: # If we're not consuming average score, we're consuming joined comments 
                    self._middleware.start_consuming(
                        self._recv_joined_post_comments_queue_config, self.process_post_comments, self.__post_comments_stream_end_callback, self.entity_sub_id)

            except ChannelClosed:
                break
    
    def __post_avg_score_stream_end_callback(self):
        self._consuming_post_avg_score = False
        self._middleware.stop_consuming()
    
    def __post_comments_stream_end_callback(self):
        self._middleware.send_termination(self._send_exchanges, {
                                            "type": FINISH_PROCESSING_TYPE})
        self.__reset_state()
        self._middleware.stop_consuming()


    def stop(self):
        self.keep_running = False
        self._middleware.stop_consuming()
        self._middleware.close()

    def process_post_avg_score(self, payload):
        self._post_avg_score = float(payload["post_avg_score"])

    def process_post_comments(self, post_comment):
        if float(post_comment["score"]) <= self._post_avg_score or post_comment["post_id"] in self._posts_already_sent or len(self._student_regexp.findall(post_comment["body"])) == 0:
            # logging.debug("discarding post_comment {}".format(
            # post_comment, post_comment["score"], self._post_avg_score))
            return

        result = {
            "type": STUDENT_LIKED_POST_WITH_SCORE_AVG_HIGHER_THAN_MEAN_TYPE, "post_id": post_comment["post_id"], "url": post_comment["url"], "score": post_comment["score"]}

        # logging.debug("Result: {}".format(result))
        self._posts_already_sent.add(post_comment["post_id"])
        self._middleware.send(self._send_exchanges, result)

    def get_backupable_state(self):
        return {
            "post_avg_score": self._post_avg_score,
            "posts_already_sent": list(self._posts_already_sent),
            "consuming_post_avg_score": self._consuming_post_avg_score
        }
    
    def __recover_backup_state(self):
        backup_state = self._middleware.recover_user_backup_state()
        if not backup_state:
            logging.info("Backup state not found. Starting from scratch.")
            return
        
        try:
            self._post_avg_score = backup_state["post_avg_score"]
            self._posts_already_sent = set(backup_state["posts_already_sent"])
            self._consuming_post_avg_score = backup_state["consuming_post_avg_score"]
            logging.info("Found and recovered backup state.")

        except Exception as e:
            logging.error(f"Error recovering backup state: {e}")
            self.__reset_state()
            return