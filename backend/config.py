# CONFIG
##################################################################

from backend.filestore.local_filestore import LocalSQLiteFileStore
from backend.ingestors.text_ingestor import TextIngestor
from backend.vector_store.local_vec_store import ChromaDBVectorStore
from backend.chunker.recursive_chunker import RecursiveChunker

TEXT_INGESTORS = TextIngestor(accepted_format=["txt","md"])
CHUNKER = RecursiveChunker(chunk_size=512,overlap=64)
VECTOR_STORE = ChromaDBVectorStore()
FILE_STORE = LocalSQLiteFileStore()

##################################################################