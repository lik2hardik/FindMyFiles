from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from typing import Annotated
from backend.filestore.filestore import IngestableFile
from backend.ingestors.ingestor import Ingestor
from backend.tasks import process_ingest_file
from backend.config import FILE_STORE

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

    ingestable_file = IngestableFile(file.file,file.filename)

    if ingestable_file.extension in Ingestor.accepted_formats:
        file_id = FILE_STORE.store(ingestable_file)
        task = process_ingest_file.delay(file_id)
        return {
            "message": "Task has been sent to the background worker pool",
            "task_id": task.id
        }
    return {"acceptable_formats": Ingestor.accepted_formats}
