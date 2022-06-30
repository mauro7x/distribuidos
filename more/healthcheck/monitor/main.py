import zmq
import signal
from typing import Dict, List, Set
from time import sleep, time

PORT = 3000
SLEEP_SECS = 3
RESPONSE_TIMEOUT_SECS = 1


class Monitor:
    def __init__(self, hosts: List[str]):
        self.__init_state(hosts)
        self.__init_connections()
        self.__init_signal_handlers()

    def __init_state(self, hosts: List[str]):
        self.__hosts = set(hosts)
        self.__alive = set(hosts)
        self.__restarting = set()

    def __init_connections(self):
        self.__context = zmq.Context()
        self.__sockets: Dict[str, zmq.Socket] = {}
        self.__poller = zmq.Poller()
        for host in self.__hosts:
            socket = self.__context.socket(zmq.REQ)
            socket.connect(f'tcp://{host}:{PORT}')
            self.__poller.register(socket, zmq.POLLIN)
            self.__sockets[host] = socket

    def __init_signal_handlers(self):
        handler = lambda *_: self.stop()
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)

    def stop(self):
        self.__context.destroy(0)
        exit(0)

    def run(self):
        while True:
            print('Running iteration...')
            dead = self.__run_iteration()
            print('Iteration finished!')
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

    def __handle_dead_nodes(self, dead: Set[str]):
        if not dead:
            return

        print('Here we should restart dead nodes:', dead)
        self.__restarting.update(dead)


def main():
    hosts = [
        'node_1',
        'node_2',
        'node_3'
    ]
    monitor = Monitor(hosts)
    monitor.run()


if __name__ == "__main__":
    main()
