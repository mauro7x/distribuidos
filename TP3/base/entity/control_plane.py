from constants import BASE_CONFIG_FILE
from common.utils import read_json, initialize_log
from common.healthcheck_listener import HealthcheckListener


def main():
    config = read_json(BASE_CONFIG_FILE)
    initialize_log(config["logging_level"])
    port: int = config["healthcheck"]["port"]
    listener = HealthcheckListener(port)
    listener.run()
