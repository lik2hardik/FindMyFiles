from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from typing import Annotated
from backend.filestore.filestore import IngestableFile
from backend.ingestors.ingestor import Ingestor

# CONFIG
##################################################################

from backend.filestore.local_filestore import LocalSQLiteFileStore
from backend.ingestors.text_ingestor import TextIngestor
from backend.vector_store.local_vec_store import ChromaDBVectorStore
from backend.chunker.recursive_chunker import RecursiveChunker

TEXT_INGESTORS = TextIngestor(accepted_format=["txt","md"])
CHUNKER = RecursiveChunker(chunk_size=512,overlap=64)
VECROR_STORE = ChromaDBVectorStore()
FILE_STORE = LocalSQLiteFileStore()

##################################################################

app = FastAPI()

class Query(BaseModel):
    q : str
    type: list[str] | None = None


@app.get("/")
def statistics():
    "route to return the statistics of application, i.e. Ingestion status , health etc"
    return {"Hello": "World"}


@app.post("/upload/")
async def upload_file(file: Annotated[UploadFile, File()]):
    ingestable_file = IngestableFile(file,file.filename)

    if ingestable_file.extension in Ingestor.accepted_formats:
        return {
            "filename": file.filename,
            "content_type": file.content_type,
        }
    return {"acceptable_formats": Ingestor.accepted_formats}
