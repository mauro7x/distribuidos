import docker
import time
import logging
from multiprocessing import Process
from multiprocessing.connection import Connection
from messages import Message, MessageType


class ContainerManager(Process):
    def __init__(self, conn: Connection, config):
        Process.__init__(self)
        self.__client = docker.from_env()
        self.__conn = conn
        self.__restart_timeout_secs: int = config["restart_timeout_secs"]
        self.__restart_retries: int = config["restart_retries"]
        self.__restart_wait_sleep_secs: int = config["restart_wait_sleep_secs"]

    def run(self):
        while True:
            msg: Message = self.__conn.recv()
            if msg.type == MessageType.EOF:
                break
            elif msg.type == MessageType.DEAD_NODE:
                self.__reset_node(msg.payload)
            else:
                logging.critical('Unknown message received')
                exit(-1)

    def __ack_reset_node(self, node: str):
        msg = Message(MessageType.NODE_RESET, node)
        self.__conn.send(msg)

    def __reset_node(self, node: str):
        logging.debug(f'Restarting node <{node}>...')
        container = self.__client.containers.get(node)
        if container.status == 'running':
            logging.debug(
                f'Node <{node}> believed to be dead but found running')
            return self.__ack_reset_node(node)

        container.start()
        retries = 0
        start = time.time()
        now = start
        while container.status != 'running':
            remaining_timeout = self.__restart_timeout_secs - (now - start)
            time.sleep(min(self.__restart_wait_sleep_secs, remaining_timeout))
            now = time.time()
            if now - start > self.__restart_timeout_secs:
                if retries < self.__restart_retries:
                    container.start()
                    retries += 1
                    start = now
                else:
                    logging.error(f'Failed to restart node <{node}>')
                    msg = Message(MessageType.FAILED, node)
                    self.__conn.send(msg)
                    return
            container = self.__client.containers.get(node)

        logging.info(f'Node <{node}> restarted successfully')
        self.__ack_reset_node(node)
