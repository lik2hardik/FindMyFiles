from abc import abstractmethod, ABC


class FileStore(ABC):
    def __init__(self, path: str = None):
        self.path = path

    @abstractmethod
    def get(self, path):
        "returns the file given the path of the file."
        pass

    @abstractmethod
    def store(self, file):
        "stores file on the system"
