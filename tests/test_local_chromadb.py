import pytest
from backend.vector_store.local_vec_store import ChromaDBVectorStore
from backend.chunker.recursive_chunker import RecursiveChunker
from backend.ingestors.text_ingestor import TextIngestor
from backend.filestore.filestore import IngestableFile



@pytest.mark.asyncio
async def test_chunks_added_properly(tmp_path):
    test_file = "tests/test.txt"

    with open(test_file, "r") as f:
        ingestable = IngestableFile(f)
        ingestor = TextIngestor(accepted_format=["txt"])
        text, metadata = await ingestor.extract_text(ingestable)

    chunker = RecursiveChunker()
    chunks = await chunker.split_text(text)
    
    assert len(chunks) > 0, "Chunker returned 0 chunks"

    vec_store = ChromaDBVectorStore(path=str(tmp_path))
    
    await vec_store.add(chunks, metadatas=[metadata] * len(chunks))

    
    # Assert A: The collection count matches the number of chunks we inserted
    assert vec_store.collection.count() == len(chunks)

    # Assert B: We can successfully retrieve data from the store
    results = await vec_store.get(query=chunks[0], k=1)
    
    # Verify that ChromaDB returned at least one document
    assert len(results["documents"][0]) > 0

    # Verify the retrieved document matches our query text
    assert results["documents"][0][0] == chunks[0]
    


    


# Which professor at the University of Ingolstadt encourages Victor's interest in natural philosophy, contrasting with M. Krempe's dismissal?