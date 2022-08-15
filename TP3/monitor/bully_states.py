import logging
from multiprocessing import Process

from time import sleep

from bully_constants import *
from data_plane import main as data_plane_main


class State:
    def __init__(self, bully_executor):
        self.bully_executor = bully_executor
        logging.info("Switching to new state: {}".format(self.state_rep))


class ElectingLeader(State):
    def __init__(self, bully_executor):
        self.state_rep = "ElectingLeader"
        self.elected_leader = None
        super().__init__(bully_executor)

    def run(self):
        self.ack_received = False
        expected_responding_peers = self.send_election()
        self.wait_for_election_responses(expected_responding_peers)

    def send_election(self):
        logging.info("Starting new leader election")
        higher_peers = self.bully_executor.get_available_higher_peers()
        for peer_id in higher_peers:
            logging.debug("Sending ELECTION to {}".format(peer_id))
            self.bully_executor.send(peer_id, ELECTION)
        return higher_peers

    def wait_for_election_responses(self, expected_responding_peers):
        responding_peers = self.bully_executor.poll_responses(
            self.handle_election_responses, self.bully_executor.config["election_response_timeout_ms"])

        logging.debug("expected_responding_peers: {} responding_peers: {} ack_recved: {} elected_leader: {}".format(
                      list(expected_responding_peers), responding_peers, self.ack_received, self.elected_leader))

        if self.elected_leader:
            logging.info("Leader elected! New leader: {}".format(
                self.elected_leader))
            return self.bully_executor.change_state(
                FollowingLeader(self.bully_executor, self.elected_leader))

        if not responding_peers or not self.ack_received:
            logging.info(
                "Got no ack from peers. Announcing myself as leader...")
            return self.bully_executor.change_state(
                AnnouncingLeadership(self.bully_executor))

        logging.info(
            "Received ACK(s) but no coordinator announced yet. Starting leader election again...")
        return self.run()

    def handle_election_responses(self, id, msg_op):
        if msg_op == ELECTION:
            assert(self.bully_executor.id > id)
            logging.debug(
                "Received ELECTION from {} - Sending ELECTION_ACK as response".format(id))
            self.bully_executor.send(id, ELECTION_ACK)
            return

        if msg_op == ELECTION_ACK:
            assert(self.bully_executor.id < id)
            logging.debug(
                "Received ELECTION_ACK from {} - Setting ack_received to True".format(id))
            self.ack_received = True
            return

        if msg_op == COORDINATOR:
            if self.bully_executor.id < id:
                logging.debug(
                    "Received COORDINATOR from {} - Setting elected_leader".format(id))
                self.elected_leader = id
                self.bully_executor.send(id, COORDINATOR_ACK)
            else:
                logging.debug(
                    "Received COORDINATOR from {} but I am higher than him - I will bully him".format(id))
            return

        if msg_op == HEALTH_CHECK:
            assert(self.bully_executor.id > id)
            logging.debug(
                "Received HEALTH_CHECK from {} - Responding HEALTH_CHECK_ACK (Seems I was leader but I have restarted)".format(id))
            self.bully_executor.send(id, HEALTH_CHECK_ACK)
            return

        error_str = "[{}] Useless message received ({}) from {} - probably sent/recved late".format(
            self.state_rep, msg_op, id)
        logging.warn(error_str)


class AnnouncingLeadership(State):
    def __init__(self, bully_executor):
        self.state_rep = "AnnouncingLeadership"
        self.coordinator_wait_recved = False
        super().__init__(bully_executor)

    def run(self):
        keep_announcing = True
        while keep_announcing:
            self.broadcast_new_coordinator()
            self.wait_for_coordination_ack()
            keep_announcing = self.coordinator_wait_recved
            self.coordinator_wait_recved = False
        self.bully_executor.change_state(Leading(self.bully_executor))

    def broadcast_new_coordinator(self):
        reachable_peers = self.bully_executor.get_all_available_peers()

        logging.debug("Broadcasting I am new COORDINATOR")

        for peer_id in reachable_peers:
            self.bully_executor.send(peer_id, COORDINATOR)

        return reachable_peers

    def wait_for_coordination_ack(self):
        logging.debug("Waiting for COORDINATOR responses")
        responding_peers = self.bully_executor.poll_responses(
            self.handle_coordinator_responses, self.bully_executor.config["coordinator_response_timeout_ms"])
        logging.debug(
            "COORDINATOR_ACK responding peers: {}".format(responding_peers))

    def handle_coordinator_responses(self, id, msg_op):
        if msg_op == DISCOVERY:
            self.handle_common_discovery_message(id)
            return

        if msg_op == ELECTION:
            logging.debug(
                "Received ELECTION from {} - Sending COORDINATOR as response".format(id))
            self.bully_executor.send(id, COORDINATOR)
            return

        if msg_op == COORDINATOR_ACK:
            logging.debug(
                "Received COORDINATOR_ACK from {}".format(id))
            return

        if msg_op == COORDINATOR:
            if id > self.bully_executor.id:
                logging.debug(
                    "[BULLIED] Received COORDINATOR from {} - Following new leader...".format(id))
                self.bully_executor.change_state(
                    FollowingLeader(self.bully_executor, id))
            else:
                logging.debug(
                    "Received COORDINATOR from {} but I will bully him".format(id))
                self.bully_executor.send_msg(id, COORDINATOR)
            return

        if msg_op == HEALTH_CHECK:
            logging.debug(
                "Received HEALTH_CHECK from {} - Sending HEALTH_CHECK_ACK as response".format(id))
            self.bully_executor.send(id, HEALTH_CHECK_ACK)
            return

        if msg_op == COORDINATOR_WAIT:
            logging.info(
                "Received COORDINATOR_WAIT from {} - I will have to wait to assume leadership".format(id))
            self.coordinator_wait_recved = True
            return

        error_str = "[{}] Useless message received ({}) from {} - probably sent/recved late".format(
            self.state_rep, msg_op, id)
        logging.warn(error_str)


class FollowingLeader(State):
    def __init__(self, bully_executor, leader_id):
        self.state_rep = "FollowingLeader"
        self.health_check_ack_recved = True
        self.leader_id = leader_id
        super().__init__(bully_executor)

    def run(self):
        self.check_leader_health()

    def check_leader_health(self):
        while self.health_check_ack_recved:
            sleep(self.bully_executor.config["health_check_frequency_secs"])

            logging.debug(
                "Sending HEALTH_CHECK to COORDINATOR {}".format(self.leader_id))

            self.bully_executor.send(self.leader_id, HEALTH_CHECK)
            self.health_check_ack_recved = False
            self.bully_executor.poll_responses(
                self.handle_request, self.bully_executor.config["health_check_timeout_ms"])

        logging.info(
            "Detecting unreachable COORDINATOR {} - Starting election".format(self.leader_id))

        self.bully_executor.change_state(ElectingLeader(self.bully_executor))

    def handle_request(self, id, msg_op):
        if msg_op == HEALTH_CHECK_ACK:
            logging.debug(
                "Received HEALTH_CHECK_ACK from {}".format(id))
            self.health_check_ack_recved = True
            return

        if msg_op == ELECTION:
            logging.debug(
                "Received ELECTION from {} - Sending ELECTION_ACK as response".format(id))
            self.bully_executor.send(id, ELECTION_ACK)
            return

        if msg_op == COORDINATOR:
            if id == self.leader_id:
                logging.debug(
                    "Received COORDINATOR from {} - Sending COORDINATOR_ACK as response".format(id))
            else:
                logging.debug(
                    "Received COORDINATOR from {} - Following new leader...".format(id))
                self.leader_id = id

            self.bully_executor.send(id, COORDINATOR_ACK)
            return

        if msg_op == COORDINATOR_ACK:
            logging.debug(
                "Received COORDINATOR_ACK from {} - Ignoring because I am not coordinator anymore".format(id))
            return

        if msg_op == HEALTH_CHECK:
            logging.debug(
                "Received HEALTH_CHECK from {} - Responding but I am not coordinator anymore".format(id))
            self.bully_executor.send(id, HEALTH_CHECK_ACK)
            return

        if msg_op == ELECTION_ACK:
            logging.debug(
                "Received late ELECTION_ACK from {} - Ignoring...".format(id))
            return

        error_str = "[{}] Useless message received ({}) from {} - probably sent/recved late".format(
            self.state_rep, msg_op, id)
        logging.warn(error_str)


class Leading(State):
    def __init__(self, bully_executor):
        self.state_rep = "Leading"
        super().__init__(bully_executor)

    def run_data_plane(self):
        self.data_plane_running = True
        self.data_plane_handler = Process(target=data_plane_main)
        self.data_plane_handler.start()

    def terminate_data_plane(self):
        self.data_plane_handler.terminate()
        self.data_plane_handler.join(
            self.bully_executor.config["control_plane_join_timeout_secs"])

        if not self.data_plane_handler.is_alive():
            exitcode = self.data_plane_handler.exitcode
            logging.info(
                "Data plane terminated with exitcode {} - New leader can now asume".format(exitcode))
            self.data_plane_running = False

    def run(self):
        self.run_data_plane()
        self.respond_requests()

    def respond_requests(self):
        while self.data_plane_running:
            self.bully_executor.poll_responses(
                self.handle_request, self.bully_executor.config["coordinator_data_plane_check_frequency_ms"])
        logging.info("Data plane has been terminated - Start Election again")
        self.bully_executor.change_state(ElectingLeader(self.bully_executor))

    def handle_request(self, id, msg_op):
        if msg_op == HEALTH_CHECK:
            logging.debug(
                "Received HEALTH_CHECK from {} - Sending HEALTH_CHECK_ACK as response".format(id))
            self.bully_executor.send(id, HEALTH_CHECK_ACK)
            return

        if msg_op == ELECTION:
            logging.debug(
                "Received ELECTION from {} - Sending COORDINATOR as response".format(id))
            self.bully_executor.send(id, COORDINATOR)
            return

        if msg_op == COORDINATOR:
            logging.debug(
                "[BULLIED] Received COORDINATOR from {} - Following new leader...".format(id))

            assert(id > self.bully_executor.id)

            if self.data_plane_running:
                logging.info(
                    "Sending COORDINATOR_WAIT until control plane tear down")

                self.bully_executor.send(id, COORDINATOR_WAIT)
                self.terminate_data_plane()
                return

            # Data plane ended => we can safely change state to follow new coordinator
            logging.debug(
                "Sending COORDINATOR_ACK since control plane is already off")
            self.bully_executor.send(id, COORDINATOR_ACK)

            self.bully_executor.change_state(
                FollowingLeader(self.bully_executor, id))
            return

        if msg_op == COORDINATOR_ACK:
            logging.debug(
                "Received COORDINATOR_ACK from {}".format(id))
            return

        error_str = "[{}] Useless message received ({}) from {} - probably sent/recved late".format(
            self.state_rep, msg_op, id)
        logging.warn(error_str)

    def stop(self):
        self.terminate_data_plane()
