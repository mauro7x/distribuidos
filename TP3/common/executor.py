import signal
from multiprocessing import Process
from typing import List


class Executor:
    def __init__(self, targets):
        # Signal handling with multiprocessing explained here:
        # www.titonbarua.com/posts/2014-10-29-safe-use-of-unix-signals-with-multiprocessing-modules-in-python

        # # 1. Ignore signals
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # 2. Spawn processes with ignore handlers
        self.__processes: List[Process] = []
        for target in targets:
            process = Process(target=target)
            process.start()
            self.__processes.append(process)

        # 3. Set parent signal handlers
        handler = lambda *_: self.__term()
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)

    def __term(self):
        for process in self.__processes:
            process.terminate()

    def join(self):
        for process in self.__processes:
            process.join()
