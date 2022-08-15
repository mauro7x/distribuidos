import os
import time
import logging
from common.utils import initialize_log, read_json
from healthcheck_monitor import HealthcheckMonitor
from constants import \
    MONITOR_CONFIG_FILE, PIPELINE_CONFIG_FILE, ENTITY_SUB_ID_KEY


def get_monitor_nodes(config):
    container_name = config["container_name"]
    replicas: int = config["replicas"]
    self_id = int(os.environ[ENTITY_SUB_ID_KEY])
    ids = filter(lambda id: id != self_id, range(replicas))
    nodes = [f'{container_name}_{id}' for id in ids]

    return nodes


def get_pipeline_nodes(pipeline):
    nodes = []
    node_names = filter(
        lambda node: node not in ['exchanges', 'queues'],
        pipeline.keys()
    )
    for node_name in node_names:
        replicas: int = pipeline[node_name].get("scale")
        if replicas:
            assert replicas > 0
            for id in range(replicas):
                nodes.append(f'{node_name}_{id}')
        else:
            nodes.append(node_name)

    return nodes


def get_nodes_to_monitor(config, pipeline):
    return get_pipeline_nodes(pipeline) + get_monitor_nodes(config)


def main():
    config = read_json(MONITOR_CONFIG_FILE)
    pipeline = read_json(PIPELINE_CONFIG_FILE)
    initialize_log(config["healthcheck"]["logging_level"])

    hosts = get_nodes_to_monitor(config, pipeline)
    logging.info(f'Starting monitor with nodes: {hosts}')
    monitor = HealthcheckMonitor(hosts, config["healthcheck"])
    monitor.run()


if __name__ == "__main__":
    main()
