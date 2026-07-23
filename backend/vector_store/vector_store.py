from abc import abstractmethod, ABC
import hashlib


class VectorStore(ABC):
    def __init__(self, path: str = None):
        self.path = path

    @abstractmethod
    def add(self, chunks: list[str], metadata: dict = None):
        "store chunks in the vector database."

    @abstractmethod
    def get(self, query: str, k=10, constraints: dict = None):
        "return the relevant chunks."

    @staticmethod
    def get_md5(chunks: list[str]) -> list[str]:
        "Get the md5 for chunk to serve as unique ids for vector store."
        return [hashlib.md5(chunk.encode("utf-8")).hexdigest() for chunk in chunks]
