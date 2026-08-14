from abc import abstractmethod, ABC


class ChunkingError(Exception):
    """
    Custom exception for chunking errors.
    """

class BaseChunker(ABC):
    def __init__(self, chunk_size=512, overlap=64):
        if chunk_size <= 0 or overlap < 0:
            raise ValueError("chunk_size must be positive and overlap must be non-negative")

        self.chunk_size = chunk_size
        self.overlap = overlap

    @abstractmethod
    def split_text(self, text: str) -> list[str]:
        """
        splits the input text into chunks with overlap.
        """
        pass
