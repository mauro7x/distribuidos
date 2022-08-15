from common.executor import Executor

# main functions
from control_plane import main as control_plane_main
from data_plane import main as data_plane_main


def main():
    targets = [control_plane_main, data_plane_main]
    executor = Executor(targets)
    executor.join()


if __name__ == "__main__":
    main()
