import logging
import time

from common.middleware.middleware import Middleware
import abc

class BasicFilter(abc.ABC):
    def __init__(self, base_config, pipeline_config, service_base_name, entity_sub_id=None):
        broker_config = base_config["broker_config"]
        entity_name = base_config["entity_name"]
        entity_config = pipeline_config[entity_name]
        self.entity_name = entity_name
        self._recv_queue_config = pipeline_config["queues"][entity_config["recv_queue"]]
        self._send_exchanges = entity_config["send_exchanges"]
        self.entity_sub_id = entity_sub_id
        self._middleware = Middleware(broker_config, pipeline_config, f"{service_base_name}{'_' + entity_sub_id if entity_sub_id else ''}",self.get_backupable_state)

    @abc.abstractmethod
    def _reset_state(self):
        pass

    @abc.abstractmethod
    def _recover_backup_state_impl(self, backup_state):
        pass

    @abc.abstractmethod
    def get_backupable_state(self):
        pass

    @abc.abstractmethod
    def stream_end_callback(self):
        pass
    
    @abc.abstractmethod
    def callback(self,payload):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    def _recover_backup_state(self):
        backup_state = self._middleware.recover_user_backup_state()
        if not backup_state:
            logging.info("Backup state not found. Starting from scratch.")
            return
        
        try:
            self._recover_backup_state_impl(backup_state)
            logging.info("Found and recovered backup state.")

        except Exception as e:
            logging.error(f"Error recovering backup state: {e}")
            self._reset_state()
            return

    def run(self):
        self._start_time = time.time()
        self._middleware.start_consuming(
            self._recv_queue_config, self.callback, self.stream_end_callback, self.entity_sub_id)
