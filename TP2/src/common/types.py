class Average:
    def __init__(self):
        self.__count: int = 0
        self.__value: float = None
        self.add = self.__add_first

    def __add_first(self, value: float):
        self.__value = value
        self.__count = 1
        self.add = self.__add

    def __add(self, value: float):
        self.__count += 1
        self.__value = (self.__value * (1 - (1 / self.__count)) +
                        (value / self.__count))

    def get(self):
        return self.__value

    def __str__(self):
        return str(self.__value)

    def __len__(self):
        return self.__count
