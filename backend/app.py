from fastapi import FastAPI, File, UploadFile
import asyncio 
from pydantic import BaseModel
from typing import Annotated
from backend.filestore.filestore import IngestableFile
from backend.ingestors.ingestor import Ingestor
from backend.tasks import process_ingest_file
from backend.config import FILE_STORE, VECTOR_STORE
from backend.config import APP_STATE

app = FastAPI()


class Query(BaseModel):
    q: str
    type: list[str] | None = None


@app.get("/")
def statistics():
    "route to return the statistics of application, i.e. Ingestion status , health etc"
    return {"Hello": "World"}


@app.post("/upload/")
async def upload_file(file: Annotated[UploadFile, File()]):
    ingestable_file = IngestableFile(file.file, file.filename)

    if ingestable_file.extension in Ingestor.accepted_formats:
        file_id = await asyncio.to_thread(FILE_STORE.store, ingestable_file)

        app_state_id = APP_STATE.insert_file(
                file_name=ingestable_file.file_name,
                file_type=ingestable_file.extension,
                file_status="Storage Complete"
        )
        task = process_ingest_file.delay(file_id,app_state_id)
        return {
            "message": "Task has been sent to the background worker pool",
            "task_id": task.id,
            "file_id": app_state_id
        }
    return {"acceptable_formats": Ingestor.accepted_formats}


@app.get("/get/")
def get_file(q: str = None):
    if q:
        result = VECTOR_STORE.get(q)
        return {"result": result}
    return None


@app.get("/get/all")
def get_all():
    result = VECTOR_STORE.collection.get()
    return {"result": result}
