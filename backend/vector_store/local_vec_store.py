from vector_store.vector_store import VectorStore
from chromadb import PersistentClient
from ingestors.ingestor import Metadata


class Chroma_DB_Vector_Store(VectorStore):
    def __init__(self, path="backend/data/vecstore/"):
        super().__init__(path)

        self.client = PersistentClient(self.path)
        self.collection = self.client.get_or_create_collection(
            name="my-collection", metadata={"description": "vector-store for data"}
        )

    async def add(self, chunks, metadatas: list[Metadata]):

        metadata_dicts = [m.model_dump() for m in metadatas]

        self.collection.add(
            ids=await self.get_md5(chunks), documents=chunks, metadatas=metadata_dicts
        )

    async def get(self, query, k=10, constraints=None):
        return self.collection.query(
            query_texts=[query],
            n_results=k
        )
