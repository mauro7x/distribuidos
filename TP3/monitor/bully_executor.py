import logging
import random
import select
import socket
import threading

from time import sleep, time

import bully_protocol
from bully_constants import *
from bully_protocol import *
from bully_states import ElectingLeader, AnnouncingLeadership


def get_current_milli_time():
    return round(time() * 1000)


class BullyExecutor:
    def __init__(self, id, peer_hosts, port, config):
        self.config = config
        self.id = id
        self.max_replica_id = max(peer_hosts.keys())
        self.peers_lock = threading.Lock()
        self.peers = {}
        self.port = port
        self.dead_peers = set()
        self.keep_running = True
        self.poller = select.poll()

        self.peers_addr = {}
        for (peer_id, peer_host) in peer_hosts.items():
            self.peers_addr[peer_id] = (peer_host, port)

        logging.debug("Address of replicas: {}".format(peer_hosts))

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(self.max_replica_id)
        self.accept_handler = threading.Thread(
            target=self.__accept_connections)
        self.accept_handler.start()

    def __accept_connections(self):
        logging.info("Accepting new peer connections...")
        while self.keep_running:
            c, addr = self._server_socket.accept()
            logging.debug('Got connection from {}'.format(addr))
            self.__perform_discovery_accept(c)

    def __perform_discovery_accept(self, c):
        try:
            c.settimeout(self.config["discovery_timeout_ms"])
            peer_id = bully_protocol.recv_id(c, True)
            bully_protocol.send_msg(DISCOVERY_ACK, c)
        except Exception as e:
            logging.error(
                "Acceptance discovery with a peer failed")
            logging.debug("Error: {}".format(e))
            return False
        return self.__save_new_connection(c, peer_id)

    def __perform_discovery_connect(self, c, peer_id):
        try:
            c.settimeout(self.config["discovery_timeout_ms"])
            bully_protocol.send_id(self.id, c)
            ack = bully_protocol.recv_msg(c, True)
            assert(ack == DISCOVERY_ACK)
        except Exception as e:
            logging.error(
                "Connection discovery with peer_id {} failed".format(peer_id))
            logging.debug("Error: {}".format(e))
            return False
        return self.__save_new_connection(c, peer_id)

    def __save_new_connection(self, c, peer_id):
        fileno = c.fileno()
        self.peers_lock.acquire()
        if peer_id in self.peers:
            self.peers_lock.release()
            c.close()
            return False
        self.peers[peer_id] = (c, fileno)
        self.peers_lock.release()
        self.poller.register(c, select.POLLIN)
        if peer_id in self.dead_peers:
            self.dead_peers.remove(peer_id)
        logging.info("Successfully connected to peer {}".format(peer_id))
        return True

    def __remove_connection(self, peer_id):
        logging.info("Lost connection with peer {}".format(peer_id))
        self.peers_lock.acquire()
        c, fileno = self.peers.pop(peer_id)
        self.peers_lock.release()
        self.poller.unregister(fileno)
        self.dead_peers.add(peer_id)
        try:
            c.close()
        except:
            return

    def __connect_to_replicas(self):
        logging.info("Connecting to peers...")
        n_attempts = 0
        missing_connections = set(self.get_all_peers())

        while n_attempts < self.config["n_connection_retries"]:
            self.peers_lock.acquire()
            connected_replicas = self.peers.keys()
            self.peers_lock.release()

            missing_connections -= set(connected_replicas)

            if not len(missing_connections):
                break

            for peer_id in missing_connections:
                try:
                    logging.debug(
                        "Trying to connect to peer {}".format(peer_id))
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect(self.peers_addr[peer_id])
                    self.__perform_discovery_connect(s, peer_id)
                except Exception as e:
                    logging.warn(
                        "Failed to connect to peer: {}".format(peer_id))
                    logging.debug("Error: {}".format(e))
                    continue

            retry_time = self.config["connection_frequency_secs"] + \
                random.randint(
                    0, self.config["connection_frequency_dispersion_secs"])
            logging.warn(
                "Could not connect to peers {}. Retrying in {} secs".format(list(missing_connections), retry_time))
            sleep(retry_time)

            n_attempts += 1

        if len(missing_connections):
            logging.info("Could not connect to {}".format(missing_connections))
            for missing_connection in missing_connections:
                self.dead_peers.add(missing_connection)
        else:
            logging.info("Successfully connected to all replicas")
            self.peers_lock.acquire()
            logging.debug("Peers map: {}".format(self.peers))
            self.peers_lock.release()

    def send(self, to_id, msg_byte):
        self.peers_lock.acquire()
        to_sock = self.peers.get(to_id, (None, None))[0]
        self.peers_lock.release()
        if not to_sock:
            return
        try:
            bully_protocol.send_msg(msg_byte, to_sock)
        except:
            # connection lost
            self.__remove_connection(to_id)

    def recv(self, fd):
        from_sock = None
        self.peers_lock.acquire()
        for (peer_id, (s, s_fd)) in self.peers.items():
            if fd == s_fd:
                from_sock = s
                break
        self.peers_lock.release()
        if not from_sock:
            raise Exception("Could not find socket associated to fd...")
        try:
            msg = bully_protocol.recv_msg(s)
        except:
            # connection reset
            return (peer_id, None)
        return (peer_id, msg)

    def should_i_be_leader(self):
        return self.id == self.max_replica_id

    def get_available_higher_peers(self):
        available_higher_peers = []
        self.peers_lock.acquire()
        for peer_id in self.peers.keys():
            if peer_id > self.id:
                available_higher_peers.append(peer_id)
        self.peers_lock.release()
        return available_higher_peers

    def get_all_peers(self):
        if self.id == self.max_replica_id:
            return list(range(self.max_replica_id))
        return list(range(0, self.id)) + list(range(self.id + 1, self.max_replica_id + 1))

    def get_all_available_peers(self):
        self.peers_lock.acquire()
        all_available_peers = self.peers.keys()
        self.peers_lock.release()
        return all_available_peers

    def poll_responses(self, cb, timeout=None):
        """
        cb: function that receives from_id and msg and processes the msg
        timeout: polling duration [ms] | 0 (blocking)

        Returns a list of responding ids
        """
        keep_polling = True
        responding_peers = set()

        if timeout:
            logging.debug("Polling responses with timeout {}".format(timeout))
            start_time = get_current_milli_time()

        remaining_timeout = timeout

        while keep_polling:
            socks = dict(self.poller.poll(remaining_timeout))
            if not len(socks):
                # timeout
                return responding_peers

            for fd in socks.keys():
                peer_id, msg = self.recv(fd)
                if not msg:
                    # connection lost
                    self.__remove_connection(peer_id)
                    continue
                # logging.debug("Received msg {} from {}".format(msg, peer_id))
                responding_peers.add(peer_id)
                cb(peer_id, msg)

            if timeout:
                remaining_timeout = timeout + start_time - get_current_milli_time()
                keep_polling = remaining_timeout > 0

        return responding_peers

    def change_state(self, new_state):
        self.state = new_state
        self.state.run()

    def run(self):
        self.__connect_to_replicas()
        if self.should_i_be_leader():
            self.state = AnnouncingLeadership(self)
        else:
            self.state = ElectingLeader(self)

        self.state.run()

    def stop(self):
        self.keep_running = False
        for (s, _) in self.peers.values():
            s.close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', self.port))
        s.close()
        # TODO: force accept to unblock by auto-connecting
        self.accept_handler.join()
