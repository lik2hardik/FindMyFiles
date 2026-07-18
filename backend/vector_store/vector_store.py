from abc import abstractmethod,ABC


class VectorStore(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def add(self, chunks: list[str], metadata={}):
        "store chunks in the vector database."

    @abstractmethod
    def get(self, query: str, k=10, contraints: dict = {}):
        "return the relevant chunks."
