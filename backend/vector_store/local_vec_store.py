from backend.vector_store.vector_store import VectorStore
from chromadb import PersistentClient
from backend.ingestors.ingestor import Metadata


class ChromaDBVectorStore(VectorStore):
    def __init__(self, path="backend/data/vecstore/"):
        super().__init__(path)
        self._client = None
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._client = PersistentClient(path=self.path)
            self._collection = self._client.get_or_create_collection(
                name="my-collection",
                metadata={"description": "vector-store for data"},
            )
        return self._collection

    def add(self, chunks, metadatas: list[Metadata]):
        metadata_dicts = [m.model_dump() for m in metadatas]
        self.collection.add(
            ids=self.get_md5(chunks), documents=chunks, metadatas=metadata_dicts
        )

    def get(self, query, k=10, constraints=None):
        return self.collection.query(query_texts=[query], n_results=k)