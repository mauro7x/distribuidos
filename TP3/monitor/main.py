from constants import MONITOR_CONFIG_FILE
from common.executor import Executor
from common.utils import read_json, initialize_log
from common.healthcheck_listener import HealthcheckListener
from control_plane import main as control_plane_main


def healthcheck_listener_main():
    config = read_json(MONITOR_CONFIG_FILE)["healthcheck"]
    initialize_log(config["logging_level"])
    port: int = config["port"]
    listener = HealthcheckListener(port)
    listener.run()


def main():
    targets = [control_plane_main, healthcheck_listener_main]
    executor = Executor(targets)
    executor.join()


if __name__ == "__main__":
    main()
