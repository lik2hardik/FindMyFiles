from abc import abstractmethod, ABC


class VectorStore(ABC):
    def __init__(self, path: str = None):
        self.path = path

    @abstractmethod
    def add(self, chunks: list[str], metadata: dict = None):
        "store chunks in the vector database."

    @abstractmethod
    def get(self, query: str, k=10, constraints: dict = None):
        "return the relevant chunks."
