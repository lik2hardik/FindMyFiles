# CONFIG
##################################################################

from backend.filestore.local_filestore import LocalSQLiteFileStore
from backend.ingestors.text_ingestor import TextIngestor
from backend.ingestors.image_ingestor import ImageOCRIngestor
from backend.vector_store.local_vec_store import ChromaDBVectorStore
from backend.chunker.recursive_chunker import RecursiveChunker
import dotenv

import os

GROQ_KEY = dotenv.dotenv_values("GROQ_KEY")

TEXT_INGESTORS = TextIngestor(accepted_format=["txt", "md"])
TEXT_INGESTORS = ImageOCRIngestor(accepted_format=["txt", "md"],
                                  GROQ_KEY=GROQ_KEY,
                                  use_api=True)

CHUNKER = RecursiveChunker(chunk_size=512, overlap=64)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
VECSTORE_DIR = os.path.join(DATA_DIR, "vecstore")
FILESTORE_DIR = os.path.join(DATA_DIR, "filestore")

VECTOR_STORE = ChromaDBVectorStore(path=VECSTORE_DIR)

FILE_STORE = LocalSQLiteFileStore(path=FILESTORE_DIR)

##################################################################
