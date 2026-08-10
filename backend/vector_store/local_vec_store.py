from backend.vector_store.vector_store import VectorStore
from backend.ingestors.ingestor import Metadata
import chromadb
from functools import cached_property


class ChromaDBVectorStore(VectorStore):
    @cached_property
    def client(self):
        return chromadb.HttpClient(host=self.host, port=self.port)

    @cached_property
    def collection(self):
        return self.client.get_or_create_collection(
            name="my-collection",
            metadata={"description": "vector-store for data"},
        )

    def __init__(self, path="backend/data/vecstore/", host="localhost", port=8001):
        super().__init__(path)
        self.host = host
        self.port = port

    def add(self, chunks, metadatas: list[Metadata]):
        metadata_dicts = [m.model_dump() for m in metadatas]
        self.collection.add(
            ids=self.get_md5(chunks), documents=chunks, metadatas=metadata_dicts
        )
        print(self.collection.count())

    def get(self, query, k=10, constraints=None):
        print(self.collection.count())
        kwargs = {
            "query_texts": [query],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"],
        }
        if constraints:
            kwargs["where"] = constraints
        return self.collection.query(**kwargs)
