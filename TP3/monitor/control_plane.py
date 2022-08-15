#!/usr/bin/env python3

import signal
import logging
import json
import os

from functools import partial
from bully_executor import BullyExecutor
from common.utils import read_json, initialize_log

BASE_CONFIG_FILE = "config.json"


def __sigterm_handler(signum, frame, bully_executor):
    logging.info(
        "Signal {} received: ending gracefully...".format(signal.Signals(signum).name))
    bully_executor.stop()
    os._exit(0)


def parse_replicas_addr(entity_name, entity_sub_id, n_replicas):
    peer_hosts = {}
    for n_replica in range(n_replicas):
        if n_replica == entity_sub_id:
            continue

        peer_hosts[n_replica] = "{}_{}".format(
            entity_name, n_replica)

    return peer_hosts


def main():
    config = read_json(BASE_CONFIG_FILE)
    initialize_log(config["control"]["logging_level"])

    logging.info("Running monitor control plane")

    entity_name = os.environ["ENTITY_NAME"]
    entity_sub_id = int(os.environ["ENTITY_SUB_ID"])

    peer_hosts = parse_replicas_addr(
        entity_name, entity_sub_id, config["replicas"])

    bully_executor = BullyExecutor(
        entity_sub_id, peer_hosts, config["control"]["port"], config["control"]["bully_config"])

    sigterm_handler = partial(
        __sigterm_handler, bully_executor=bully_executor)
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    bully_executor.run()


if __name__ == "__main__":
    main()
