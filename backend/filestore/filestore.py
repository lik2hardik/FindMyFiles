from abc import abstractmethod


class FileStore:
    def __init__(self):
        pass

    @abstractmethod
    def get(self, path):
        "returns the file given the path of the file."
        pass

    @abstractmethod
    def store(self, file):
        "stores file on the system"
