from fastapi import FastAPI, File, HTTPException, UploadFile
import asyncio
from typing import Annotated
from backend.filestore.filestore import IngestableFile
from backend.ingestors.ingestor import Ingestor
from backend.tasks import process_ingest_file
from backend.config import FILE_STORE, VECTOR_STORE, APP_STATE
from backend.search import SearchRequest, build_where, shape_search_response

app = FastAPI()


@app.get("/")
def statistics():
    "route to return the statistics of application, i.e. Ingestion status , health etc"
    return APP_STATE.get_status_all()


@app.post("/upload/")
async def upload_file(file: Annotated[UploadFile, File()]):
    ingestable_file = IngestableFile(file.file, file.filename)

    if ingestable_file.extension in Ingestor.accepted_formats:
        file_id = await asyncio.to_thread(FILE_STORE.store, ingestable_file)

        app_state_id = APP_STATE.insert_file(
            file_name=ingestable_file.file_name,
            file_type=ingestable_file.extension,
            file_status="Storage Complete",
        )
        task = process_ingest_file.delay(file_id, app_state_id)
        return {
            "message": "Task has been sent to the background worker pool",
            "task_id": task.id,
            "file_id": app_state_id,
        }
    return {"acceptable_formats": Ingestor.accepted_formats}


@app.post("/search/")
def search(request: SearchRequest):
    if request.extension:
        unknown = [
            ext for ext in request.extension if ext not in Ingestor.accepted_formats
        ]
        if unknown:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Unsupported file extension(s)",
                    "unknown_extensions": unknown,
                    "acceptable_formats": Ingestor.accepted_formats,
                },
            )

    if request.date_from and request.date_to and request.date_from > request.date_to:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "date_from must be before date_to",
                "date_from": request.date_from.isoformat(),
                "date_to": request.date_to.isoformat(),
            },
        )

    where = build_where(request.extension, request.date_from, request.date_to)
    raw = VECTOR_STORE.get(request.q, k=request.k, constraints=where)
    return shape_search_response(raw, request)


@app.get("/files/")
def list_files():
    return APP_STATE.get_status_all()


@app.get("/files/{file_id}")
def file_status(file_id: int):
    try:
        return APP_STATE.get_status_by_id(file_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e