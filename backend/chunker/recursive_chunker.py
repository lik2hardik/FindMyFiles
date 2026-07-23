from langchain_text_splitters import RecursiveCharacterTextSplitter
from .chunker import Chunker


class RecursiveChunker(Chunker):
    def __init__(self, chunk_size=512, overlap=64):
        super().__init__(chunk_size, overlap)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap,
            separators=["\n\n", "\n", " ", ""],
        )

    def split_text(self, text: str):
        chunks = self.splitter.split_text(text)
        return chunks
