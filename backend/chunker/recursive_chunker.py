from langchain_text_splitters import RecursiveCharacterTextSplitter
from .base_chunker import BaseChunker, ChunkingError
from functools import cached_property


class RecursiveChunker(BaseChunker):
    def __init__(self, chunk_size=512, overlap=64):
        super().__init__(chunk_size, overlap)

    @cached_property
    def splitter(self):
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap,
            separators=["\n\n", "\n", " ", ""],
        )

    def split_text(self, text: str):
        try:
            chunks = self.splitter.split_text(text)
            return chunks
        except Exception as e:
            raise ChunkingError(f"Failed to split text: {str(e)}")
