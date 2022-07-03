import signal
from multiprocessing import Process

# main functions
from control import main as controlplane_main
from data import main as dataplane_main


class Executor:
    def __init__(self, targets):
        self.__processes = [Process(target=target) for target in targets]
        self.__set_signal_handlers()

    def __set_signal_handlers(self):
        handler = lambda *_: self.__term()
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)

    def __start(self):
        for process in self.__processes:
            process.start()

    def __join(self):
        for process in self.__processes:
            process.join()

    def __term(self):
        for process in self.__processes:
            process.terminate()

    def __call__(self):
        self.__start()
        self.__join()


def main():
    processes = [controlplane_main, dataplane_main]
    executor = Executor(processes)
    executor()


if __name__ == "__main__":
    main()
