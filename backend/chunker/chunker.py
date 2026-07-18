from abc import abstractmethod,ABC


class Chunker(ABC):
    def __init__(self, chunk_size=512, overlap=64):
        self.chunk_size = chunk_size
        self.overlap = overlap

    @abstractmethod
    async def split_text(self, text: str) -> list[str]:
        """
        splits the input text into chunks with overlap.
        """
        pass
