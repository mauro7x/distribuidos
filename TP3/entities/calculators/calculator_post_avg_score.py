import logging

from common.basic_filter import BasicFilter
from common.constants import FINISH_PROCESSING_TYPE, POST_AVG_SCORE_TYPE


class Entity(BasicFilter):
    def __init__(self, base_config, pipeline_config):
        BasicFilter.__init__(
            self, base_config, pipeline_config, "calculator_post_avg_score")
        self._reset_state()
        self._recover_backup_state()


    def _reset_state(self):
        self.score_count = 0
        self.score_sum = 0

    def stream_end_callback(self):

        post_avg_score = 0

        if self.score_count:
            post_avg_score = self.score_sum / self.score_count

        result = {"type": POST_AVG_SCORE_TYPE,
                  "post_avg_score": post_avg_score}
        logging.info("Result: post_avg_score: {}".format(post_avg_score))
        self._middleware.send(self._send_exchanges, result)

        self._middleware.send_termination(self._send_exchanges, {
                                          "type": FINISH_PROCESSING_TYPE})

        self._reset_state()

    def stop(self):
        self._middleware.stop_consuming()
        self._middleware.close()

    def callback(self, input):
        # logging.debug("[{}] Received post: {}".format(
        #     self.entity_name, input))

        self.score_count += 1
        self.score_sum += int(input["score"])

        # logging.debug("[{}] Partial results - count: {} sum: {}".format(
        #     self.entity_name, self.score_count, self.score_sum))

    def get_backupable_state(self):
        return {
            "score_count": self.score_count,
            "score_sum": self.score_sum
        }

    def _recover_backup_state_impl(self,backup_state):
        self.score_count = backup_state["score_count"]
        self.score_sum = backup_state["score_sum"]