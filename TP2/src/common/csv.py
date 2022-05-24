import csv
from typing import List


class ReaderBuffer:
    def __init__(self):
        self.__buffer = []

    def __iter__(self):
        return self

    def __next__(self):
        return self.__buffer.pop()

    def add(self, data):
        self.__buffer.append(data)


class WriterBuffer:
    def __init__(self):
        self.__buffer = []

    def write(self, *args):
        data = args[0]
        self.__buffer.append(data)

    def pop(self) -> str:
        return self.__buffer.pop()


class CSVParser:
    def __init__(self):
        self.__reader_buffer = ReaderBuffer()
        self.__reader = csv.reader(self.__reader_buffer)
        self.__writer_buffer = WriterBuffer()
        self.__writer = csv.writer(self.__writer_buffer)
        self.__line_terminator = self.__reader.dialect.lineterminator

    def decode(self, line: str):
        self.__reader_buffer.add(line)
        return next(self.__reader)

    def encode(self, values: List[str]):
        self.__writer.writerow(values)
        encoded = self.__writer_buffer.pop()
        return encoded.rstrip(self.__line_terminator)
