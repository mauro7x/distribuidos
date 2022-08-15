import zmq
import signal
import logging
from multiprocessing import Pipe
from typing import Dict, List, Set
from time import sleep, time
from container_manager import ContainerManager
from messages import Message, MessageType


class HealthcheckMonitor:
    def __init__(self, hosts: List[str], config):
        self.__port: int = config["port"]
        self.__response_timeout_secs: int = config["response_timeout_secs"]
        self.__ping_frequency_secs: int = config["ping_frequency_secs"]
        self.__init_state(hosts)
        self.__init_container_manager(config["container_manager"])
        self.__init_connections()
        self.__init_signal_handlers()

    def __init_state(self, hosts: List[str]):
        self.__hosts = set(hosts)
        self.__alive = set(hosts)
        self.__restarting = set()

    def __init_container_manager(self, config):
        conn1, conn2 = Pipe(duplex=True)
        self.__container_manager = ContainerManager(conn2, config)
        self.__container_manager.start()
        self.__container_manager_conn = conn1

    def __init_connections(self):
        self.__context = zmq.Context()
        self.__sockets: Dict[str, zmq.Socket] = {}
        self.__poller = zmq.Poller()
        for host in self.__hosts:
            self.__register_node(host)

    def __init_signal_handlers(self):
        handler = lambda *_: self.stop()
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)

    def stop(self, code=0):
        eof_msg = Message(MessageType.EOF, None)
        self.__container_manager_conn.send(eof_msg)
        self.__container_manager.join()
        self.__context.destroy(0)
        exit(code)

    def run(self):
        while True:
            self.__check_reset_nodes()
            dead = self.__run_iteration()
            logging.debug(f'Iteration finished. Dead nodes: {dead}')
            self.__handle_dead_nodes(dead)
            sleep(self.__ping_frequency_secs)

    def __run_iteration(self):
        self.__send_pings()
        alive = self.__wait_responses()
        dead = self.__alive - alive
        self.__alive = alive

        return dead

    def __send_pings(self):
        logging.debug(f'Sending ping to: {self.__alive}')
        for host in self.__alive:
            socket = self.__sockets[host]
            socket.send(b'')

    def __wait_responses(self) -> Set[str]:
        alive: Set[str] = set()
        now = time()
        end = now + self.__response_timeout_secs
        while now < end:
            timeout = (end - now) * 1000
            hosts = self.__recv_ack(timeout)
            if not hosts:
                break

            alive.update(hosts)
            if len(alive) == len(self.__alive):
                break

            now = time()

        return alive

    def __recv_ack(self, timeout=None):
        try:
            socks = dict(self.__poller.poll(timeout))
        except KeyboardInterrupt:
            exit(0)

        if not socks:
            return

        hosts = []
        for host, socket in self.__sockets.items():
            if socket in socks:
                socket.recv()
                hosts.append(host)

        return hosts

    def __register_node(self, node):
        socket = self.__context.socket(zmq.REQ)
        socket.connect(f'tcp://{node}:{self.__port}')
        self.__poller.register(socket, zmq.POLLIN)
        self.__sockets[node] = socket
        logging.debug(f'Node <{node}> registered')

    def __unregister_node(self, node):
        socket = self.__sockets[node]
        socket.close()
        self.__poller.unregister(socket)
        self.__sockets.pop(node)
        logging.debug(f'Node <{node}> unregistered')

    def __handle_dead_nodes(self, dead: Set[str]):
        if not dead:
            return

        for node in dead:
            logging.warning(f'Node <{node}> is dead')
            self.__unregister_node(node)
            msg = Message(MessageType.DEAD_NODE, node)
            self.__container_manager_conn.send(msg)

        self.__restarting.update(dead)

    def __check_reset_nodes(self):
        while self.__container_manager_conn.poll():
            msg: Message = self.__container_manager_conn.recv()
            if msg.type == MessageType.NODE_RESET:
                node = msg.payload
                self.__register_node(node)
                self.__restarting.remove(node)
                self.__alive.add(node)
            elif msg.type == MessageType.FAILED:
                self.stop(code=-1)
            else:
                logging.critical('Unknown message received')
                exit(-1)
