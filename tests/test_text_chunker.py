from backend.chunker import RecursiveChunker, ChunkingError
import pytest


def test_text_ingestor_extracts_valid_chunks():
    chunker = RecursiveChunker(chunk_size=100, overlap=10)
    mock_shakespeare_text = "To be, or not to be, that is the question.\n" * 500

    splits = chunker.split_text(mock_shakespeare_text)

    assert isinstance(splits, list)
    assert len(splits) > 1

    for chunk in splits:
        assert isinstance(chunk, str)
        assert len(chunk.strip()) > 0
        assert len(chunk) <= 100


def test_invalid_chunker_init():
    with pytest.raises(ValueError):
        RecursiveChunker(chunk_size=-1, overlap=10)


def test_invalid_split_text():
    chunker = RecursiveChunker()
    with pytest.raises(ChunkingError):
        chunker.split_text(1)
