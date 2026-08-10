import time
from backend.celery_app import celery_app
from backend.ingestors.ingestor import Ingestor, IngestFailed
from backend.config import CHUNKER, FILE_STORE, VECTOR_STORE, APP_STATE


@celery_app.task(name="tasks.process_file_task")
def process_file_task(filename: str) -> str:
    """Simulates a heavy file processing task."""
    print(f"Starting processing for {filename}...")
    time.sleep(5)  # Simulate expensive work
    print(f"Finished processing {filename}!")
    return f"Success: {filename} was fully processed."


@celery_app.task(name="tasks.ingest_file")
def process_ingest_file(file_id, app_state_id) -> str:
    """Ingest the stored file end to end and return the file id."""

    file = FILE_STORE.get(file_id)

    print(f"Starting processing for {file.file_name}...")

    try:
        ingestor: Ingestor = Ingestor.ingestor_map.get(file.extension, None)

        if ingestor is None:
            raise IngestFailed(f"No ingestor found for file type: {file.extension}")

        text, metadata = ingestor.extract_text(file)
        APP_STATE.update_file(app_state_id, "Ingestion Complete")
        print(f"Ingestion complete for {file.file_name}...")
        text_chunks = CHUNKER.split_text(text)
        APP_STATE.update_file(app_state_id, "Chunking Complete")
        print(f"Chunking complete for {file.file_name}...")
        VECTOR_STORE.add(text_chunks, [metadata] * len(text_chunks))
        APP_STATE.update_file(app_state_id, "Embedding Complete")
        print(f"Vector embeddings complete for {file.file_name}...")
        APP_STATE.update_file(app_state_id, "Ingestion Successful")

        print(f"Finished processing {file.file_name}!")

        return 0

    except IngestFailed as e:
        APP_STATE.update_file(
            app_state_id, status="Ingestion Failed", error_msg=f"Ingestion Error: {e}"
        )
        return f"Ingestion Error: {e}"
