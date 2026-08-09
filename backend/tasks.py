import time
from backend.celery_app import celery_app
from backend.ingestors.ingestor import Ingestor, IngestFailed
from backend.config import get_chunker, get_file_store, get_vector_store, get_app_state


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

    file = get_file_store().get(file_id)
    app_state = get_app_state()

    print(f"Starting processing for {file.file_name}...")

    try:
        ingestor: Ingestor = Ingestor.ingestor_map.get(file.extension, None)
        text, metadata = ingestor.extract_text(file)
        app_state.update_file(app_state_id, "Ingestion Complete")
        print(f"Ingestion complete for {file.file_name}...")
        text_chunks = get_chunker().split_text(text)
        app_state.update_file(app_state_id, "Chunking Complete")
        print(f"Chunking complete for {file.file_name}...")
        get_vector_store().add(text_chunks, [metadata] * len(text_chunks))
        app_state.update_file(app_state_id, "Embedding Complete")
        print(f"Vector embeddings complete for {file.file_name}...")
        app_state.update_file(app_state_id, "Ingestion Successful")

        print(f"Finished processing {file.file_name}!")

        return 0

    except IngestFailed as e:
        app_state.update_file(
            app_state_id, status="Ingestion Failed", error_msg=f"Ingestion Error: {e}"
        )
        return f"Ingestion Error: {e}"
