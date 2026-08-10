from fastapi import FastAPI, File, HTTPException, Response, UploadFile
import asyncio
from typing import Annotated
from backend.filestore.filestore import IngestableFile
from backend.ingestors.ingestor import Ingestor
from backend.tasks import process_ingest_file
from backend.config import FILE_STORE, VECTOR_STORE, APP_STATE
from backend.search import SearchRequest, build_where, shape_search_response

app = FastAPI()

MEDIA_TYPES = {
    "txt": "text/plain",
    "md": "text/plain",
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
}


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
            file_id=file_id,
        )
        task = process_ingest_file.delay(file_id, app_state_id)
        return {
            "message": "Task has been sent to the background worker pool",
            "task_id": task.id,
            "app_state_id": app_state_id,
            "file_id": file_id,
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
    rows = APP_STATE.get_status_all()
    for row in rows:
        file_id = row.get("file_id")
        row["file_size"] = None
        if file_id is not None:
            try:
                meta = FILE_STORE.get_metadata(file_id)
                row["file_size"] = meta["size"]
            except FileNotFoundError:
                pass

        if row.get("add_timestamp") and row.get("last_update_timestamp"):
            row["duration_seconds"] = round(
                (row["last_update_timestamp"] - row["add_timestamp"]).total_seconds(), 2
            )
        else:
            row["duration_seconds"] = None
    return rows


@app.get("/file/{file_id}")
def get_file_contents(file_id: int):
    try:
        ingestable_file = FILE_STORE.get(file_id)
    except (FileNotFoundError, IOError) as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    media_type = MEDIA_TYPES.get(ingestable_file.extension, "application/octet-stream")
    file_obj = ingestable_file.file_obj
    try:
        file_obj.seek(0)
        content = file_obj.read()
    finally:
        file_obj.close()

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{ingestable_file.file_name}"'
        },
    )


@app.get("/files/{file_id}")
def file_status(file_id: int):
    try:
        return APP_STATE.get_status_by_id(file_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
