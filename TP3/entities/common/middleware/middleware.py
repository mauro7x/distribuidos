import json
import logging
import os
import pika
import time

from operator import itemgetter
from common.constants import FINISH_PROCESSING_TYPE
from common.middleware.protocol import BrokerProtocol
from common.middleware.send_strategies import StrategyBuilder
from common.middleware.backup import Backup


class Middleware:
    def __init__(self, broker_config, pipeline_config, service_name, get_backupable_user_state=lambda: {}, recover_backup = True):
        # Reduce pika info logging noise
        logging.getLogger("pika").setLevel(logging.WARNING)

        n_connect_attempt = 0
        connected = False

        # give some time for broker to initialize
        time.sleep(broker_config["freq_retry_connect"])

        while not connected:
            try:
                self._connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=broker_config["host"]))
                self._channel = self._connection.channel()

                connected = True
                logging.info("Successfully connected to broker.")
            except:
                if n_connect_attempt >= broker_config["n_connect_attempts"]:
                    raise

                logging.warn("Broker not ready. Retrying connection in %d secs. [%d/%d]" % (
                    broker_config["freq_retry_connect"], n_connect_attempt, broker_config["n_connect_attempts"]))

                n_connect_attempt += 1
                time.sleep(broker_config["freq_retry_connect"])
                continue

        self._batch_size = broker_config["batch_size"]
        self._backup_on_flush = broker_config["backup_on_flush"]
        self._pipeline_config = pipeline_config
        self.__initialize_pipeline()
        self._send_strategies = {}
        self.service_name = service_name


        self.backup = Backup(service_name, get_backupable_user_state, self.__get_backupable_middleware_state)
        self._backup_period = broker_config["backup_period"]

        self._n_pending_end_messages = {}
        self.__reset_state()

        # These are only stored for debugging purposes
        self._sent_terminations = 0

        if recover_backup:
            self.__recover_backup_state()

    def __reset_state(self):
        self._consuming = False
        self._batches = {}
        self._last_sent_id = {}
        self._last_received_id = {}
        self._unacked_messages = []

    def __initialize_pipeline(self):
        """
        Pipeline idempotent initialization for all entities.
        Creates exchanges and queues and their bindings, as specified in pipeline_config
        """
        logging.info("Initializing pipeline")

        for exchange_config in self._pipeline_config["exchanges"].values():
            self.__declare_exchange(exchange_config)

        for queue_config in self._pipeline_config["queues"].values():
            queue_base_name = queue_config["name"]
            scale_entity = queue_config.get("scale_based_on_entity")

            if not scale_entity:
                self.__declare_and_bind_queue(
                    queue_base_name, queue_config)
                continue

            n_queues = self._pipeline_config[scale_entity]["scale"]

            for routing_key in range(n_queues):
                queue_name = "{}_{}".format(queue_base_name, routing_key)
                self.__declare_and_bind_queue(
                    queue_name, queue_config, str(routing_key))

        logging.info("Pipeline initialized successfully")

    def __declare_exchange(self, exchange_config):
        name, exchange_type, durable, auto_delete = itemgetter(
            'name', 'type', 'durable', 'auto_delete')(exchange_config)

        self._channel.exchange_declare(exchange=name, exchange_type=exchange_type,
                                       durable=durable, auto_delete=auto_delete)

    def __declare_and_bind_queue(self, queue_name, queue_config, routing_key=''):
        durable, exclusive, auto_delete, bind_to_exchange = itemgetter(
            'durable', 'exclusive', 'auto_delete', 'bind_to_exchange')(queue_config)

        self._channel.queue_declare(queue=queue_name, durable=durable,
                                    exclusive=exclusive, auto_delete=auto_delete)

        self._channel.queue_bind(
            exchange=bind_to_exchange, queue=queue_name, routing_key=routing_key)

    def __consume_from_queue(self, queue_name, queue_config, consume_cb, stream_end_callback):

        # Make sure we don't override recovered backup data
        if queue_name not in self._n_pending_end_messages:
            self._n_pending_end_messages[queue_name] = int(queue_config.get(
                "n_end_messages", "1"))

        def cb_wrapper(ch, method, properties, body):
            service_name, id, deserialized_body = BrokerProtocol.deserialize(body)

            # Check for duplicates. id = -1 means duplicate check should be skipped
            if id <= self._last_received_id.get((service_name,queue_name), 0) and id != -1:
                logging.debug(f"[Middleware] Duplicate message {id} received. Skipping.")
                self._channel.basic_ack(delivery_tag=method.delivery_tag)
                return

            if id != -1: 
                self._last_received_id[(service_name,queue_name)] = id

            # Save the delivery tag
            self._unacked_messages.append(method.delivery_tag)
            received_end = False
            received_termination = False

            if deserialized_body.get("type") == FINISH_PROCESSING_TYPE:
                self._n_pending_end_messages[queue_name] -= 1
                received_termination = True

                if not self._n_pending_end_messages[queue_name]:
                    logging.info("Terminating...")

                    stream_end_callback()

                    self._n_pending_end_messages[queue_name] = int(queue_config.get(
                        "n_end_messages", "1"))

                    received_end = True
                else:
                    logging.debug("Received termination. Pending terminations: {}".format(
                        self._n_pending_end_messages[queue_name]))
            else:
                # Process the data in the batch
                for payload in deserialized_body["batch"]:
                    consume_cb(payload)

            if len(self._unacked_messages) >= self._backup_period or received_end or received_termination:
                self.backup.stage()
                self.__flush_all_batches(must_be_full=True)
                self.backup.commit()

                if received_end:
                    self.__reset_state()
                    self.backup.stage()
                    self.backup.commit()
                # Ack the message using the delivery tag
                self.__ack_all()
            


        auto_ack, exclusive = itemgetter(
            'auto_ack', 'exclusive')(queue_config)

        self._channel.basic_consume(
            queue=queue_name, on_message_callback=cb_wrapper, auto_ack=auto_ack, exclusive=exclusive)

        if not self._consuming:
            self._consuming = True
            self._channel.start_consuming()

    def __get_next_routing_key(self, exchange_name, payload):
        if not exchange_name in self._send_strategies:
            strategy = self._pipeline_config["exchanges"][exchange_name].get("strategy", {
                "name": "default"})
            n_routing_keys = self._pipeline_config["exchanges"][exchange_name].get(
                "n_routing_keys", 1)
            # logging.debug("[Middleware] Creating strategy {} for exchange {}".format(
            #     strategy, exchange_name))
            self._send_strategies[exchange_name] = StrategyBuilder.build(
                strategy, n_routing_keys)

        strategy = self._send_strategies[exchange_name]
        return strategy.get_routing_key(payload)

    def __get_all_routing_keys(self, exchange_name):
        n_routing_keys = self._pipeline_config["exchanges"][exchange_name].get(
            "n_routing_keys")
        if not n_routing_keys:
            return [""]
        return [str(routing_key) for routing_key in range(n_routing_keys)]

    def __pack_payload(self, payload, exchange_name, routing_key, skip_deduplication = False):
        if skip_deduplication:
            message_id = -1
        else:
            self._last_sent_id[(exchange_name, routing_key)] = self._last_sent_id.get((exchange_name, routing_key), 0) + 1
            message_id = self._last_sent_id[(exchange_name, routing_key)]
        
        payload = (self.service_name, message_id, payload)
        return BrokerProtocol.serialize(payload)

    def __send_batch(self, exchange_name, batch, routing_key):
        payload = {"batch": batch}
        raw_payload = self.__pack_payload(payload, exchange_name, routing_key)

        self._channel.basic_publish(
            exchange=exchange_name, routing_key=routing_key, body=raw_payload)

    def __send(self, exchange_name, routing_key, payload, wrap_in_batch = True, skip_deduplication = False):
        if not wrap_in_batch:
            raw_payload = self.__pack_payload(payload, exchange_name, routing_key, skip_deduplication)
            self._channel.basic_publish(
                exchange=exchange_name, routing_key=routing_key, body=raw_payload)
            return

        batch = self._batches.get((exchange_name, routing_key), [])
        batch.append(payload)
        self._batches[(exchange_name, routing_key)] = batch

        if len(batch) >= self._batch_size:
            if self._backup_on_flush:
                self.backup.stage()
                self.__flush_all_batches(must_be_full=True)
                self.backup.commit()
                self.__ack_all()
            else:
                self.__send_batch(exchange_name, batch, routing_key)
                self._batches[(exchange_name, routing_key)] = []

    def send(self, exchanges, payload):
        for exchange_name in exchanges.keys():
            routing_key = self.__get_next_routing_key(exchange_name, payload)

            self.__send(exchange_name, routing_key, payload, True)

    def send_termination(self, exchanges, payload, skip_deduplication = False):
        # Check if there is a pending batch. If so, send it
        self._sent_terminations += 1
        self.backup.stage()

        self.__flush_all_batches()

        for exchange_name in exchanges.keys():
            for routing_key in self.__get_all_routing_keys(exchange_name):
                self.__send(exchange_name, routing_key,
                            payload, False, skip_deduplication)
        
        self.backup.commit()
        self.__ack_all()

    def start_consuming(self, recv_queue_config, consume_cb, stream_end_callback, entity_sub_id=None):
        '''
        consume_cb and stream_end_callback are guaranteed to be called before 
        data is backed up, and before message is ack'd to the broker.
        '''
        queue_name = recv_queue_config["name"]
        if entity_sub_id:
            queue_name += "_{}".format(entity_sub_id)

        self.__consume_from_queue(
            queue_name, recv_queue_config, consume_cb, stream_end_callback)

    def stop_consuming(self):
        if self._consuming:
            self._channel.stop_consuming()
            self._consuming = False

    def close(self):
        self._channel.close()
        self._connection.close()

    def __get_backupable_middleware_state(self):
        # Any middleware state that needs to be backed up should be added here
        return {
            "n_pending_end_messages": self._n_pending_end_messages,
            "last_sent_id": self._last_sent_id,
            "last_received_id": self._last_received_id,
            "batches": self._batches,
            "sent_terminations": self._sent_terminations
        }

    def recover_user_backup_state(self):
        return self.backup.recover_backup_state('user')

    def __recover_backup_state(self):
        backup_state = self.backup.recover_backup_state('middleware')
        if not backup_state:
            return
        try:
            self._n_pending_end_messages = backup_state['n_pending_end_messages']
            self._last_sent_id = backup_state['last_sent_id']
            self._last_received_id = backup_state['last_received_id']
            self._batches = backup_state['batches']
            self._sent_terminations = backup_state['sent_terminations']
            logging.debug("Recovered backed up middleware state successfully")
        except Exception as e:
            logging.warn(f"Problem restoring backed up middleware state: {e}")

    def __flush_all_batches(self, must_be_full = False):
        for (exchange_name, routing_key), batch in self._batches.items():
            if (must_be_full and len(batch) >= self._batch_size) or (not must_be_full and len(batch) > 0):
                self.__send_batch(exchange_name, batch, routing_key)
                self._batches[(exchange_name, routing_key)] = []
    
    def __ack_all(self):
        for unacked_message in self._unacked_messages:
            self._channel.basic_ack(delivery_tag=unacked_message)
        self._unacked_messages = []

    def force_backup(self):
        self.backup.stage()
        self.__flush_all_batches(must_be_full=True)
        self.backup.commit()

        # Ack the message using the delivery tag
        self.__ack_all()