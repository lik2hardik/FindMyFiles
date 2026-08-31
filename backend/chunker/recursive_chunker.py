from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.sql.selectable import elem
from .base_chunker import BaseChunker, ChunkingError
from functools import cached_property


class RecursiveChunker(BaseChunker):
    def __init__(self, chunk_size=512, overlap=64):
        try:
            super().__init__(chunk_size, overlap)
        except Exception as e:
            raise ChunkingError(f"Failed to initialize RecursiveChunker :{e}") from e

    @cached_property
    def splitter(self):
        try:
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.overlap,
                separators=["\n\n", "\n", " ", ""],
            )
        except Exception as e:
            raise ChunkingError("Failed to Initialize RecursiveCharacterTextSplitter") from e


    def split_text(self, text: str):
        try:
            chunks = self.splitter.split_text(text)
            return chunks
        except Exception as e:
            raise ChunkingError(f"Failed to split text: {str(e)}") from e
