from backend.vector_store.vector_store import VectorStore
from chromadb import PersistentClient
from backend.ingestors.ingestor import Metadata
import chromadb


class ChromaDBVectorStore(VectorStore):
    def __init__(self, path="backend/data/vecstore/", host="localhost", port=8001):
        super().__init__(path)
        self.host = host
        self.port = port
        self._client = None
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._client = chromadb.HttpClient(host=self.host, port=self.port)
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
        print(self.collection.count())

    def get(self, query, k=10, constraints=None):
        print(self.collection.count())
        return self.collection.query(query_texts=[query], n_results=k)