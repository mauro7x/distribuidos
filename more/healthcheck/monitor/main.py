from dataclasses import dataclass
import zmq
import signal
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from typing import Dict, List, Optional, Set
from time import sleep, time
from enum import Enum
import docker

PORT = 3000
SLEEP_SECS = 3
RESPONSE_TIMEOUT_SECS = 1
DOCKER_RESTART_WAIT_SLEEP_TIME = 0.5
DOCKER_RESTART_WAIT_TIMEOUT = 3
DOCKER_RESTART_RETRIES = 3


class MessageType(Enum):
    EOF = 0
    DEAD_NODE = 1
    NODE_RESET = 2
    FAILED = 3


@dataclass
class Message():
    type: MessageType
    payload: Optional[str]


class ContainerManager(Process):
    def __init__(self, conn: Connection):
        Process.__init__(self)
        self.__client = docker.from_env()
        self.__conn = conn

    def run(self):
        while True:
            msg: Message = self.__conn.recv()
            if msg.type == MessageType.EOF:
                break
            elif msg.type == MessageType.DEAD_NODE:
                self.__reset_node(msg.payload)
            else:
                print('Unknown message received')
                exit(-1)

    def __reset_node(self, node: str):
        print(f'Restarting node <{node}>...')
        container = self.__client.containers.get(node)
        container.restart()

        retries = 0
        start = time()
        while container.status != 'running':
            sleep(DOCKER_RESTART_WAIT_SLEEP_TIME)
            now = time()
            if now - start > DOCKER_RESTART_WAIT_TIMEOUT:
                if retries < DOCKER_RESTART_RETRIES:
                    container.restart()
                    retries += 1
                    start = now
                else:
                    print(f'Failed to restart node <{node}>')
                    msg = Message(MessageType.FAILED, node)
                    self.__conn.send(msg)
                    return
            container = self.__client.containers.get(node)

        print(f'Node <{node}> restarted successfully')
        msg = Message(MessageType.NODE_RESET, node)
        self.__conn.send(msg)


class Monitor:
    def __init__(self, hosts: List[str]):
        self.__init_state(hosts)
        self.__init_container_manager()
        self.__init_connections()
        self.__init_signal_handlers()

    def __init_state(self, hosts: List[str]):
        self.__hosts = set(hosts)
        self.__alive = set(hosts)
        self.__restarting = set()

    def __init_container_manager(self):
        conn1, conn2 = Pipe(duplex=True)
        self.__container_manager = ContainerManager(conn2)
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
            self.__handle_dead_nodes(dead)
            sleep(SLEEP_SECS)

    def __run_iteration(self):
        self.__send_pings()
        alive = self.__wait_responses()
        dead = self.__alive - alive
        self.__alive = alive

        return dead

    def __send_pings(self):
        for host in self.__alive:
            socket = self.__sockets[host]
            socket.send(b'')

    def __wait_responses(self) -> Set[str]:
        alive: Set[str] = set()
        now = time()
        end = now + RESPONSE_TIMEOUT_SECS
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
        socket.connect(f'tcp://{node}:{PORT}')
        self.__poller.register(socket, zmq.POLLIN)
        self.__sockets[node] = socket
        print(f'Node <{node}> registered')

    def __unregister_node(self, node):
        socket = self.__sockets[node]
        socket.close()
        self.__poller.unregister(socket)
        self.__sockets.pop(node)
        print(f'Node <{node}> unregistered')

    def __handle_dead_nodes(self, dead: Set[str]):
        if not dead:
            return

        for node in dead:
            print(f'Node <{node}> is dead')
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
                print('Unknown message received')
                exit(-1)


def main():
    sleep(1)
    print('Starting monitor...')
    hosts = [
        'node_1',
        'node_2',
        'node_3'
    ]
    monitor = Monitor(hosts)
    monitor.run()


if __name__ == "__main__":
    main()
