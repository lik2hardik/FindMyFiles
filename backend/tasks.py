import time
from celery_app import celery_app
from backend.filestore.filestore import IngestableFile
from backend.ingestors.ingestor import Ingestor
from config import CHUNKER,FILE_STORE,VECTOR_STORE

@celery_app.task(name="tasks.process_file_task")
def process_file_task(filename: str) -> str:
    """Simulates a heavy file processing task."""
    print(f"Starting processing for {filename}...")
    time.sleep(5)  # Simulate expensive work
    print(f"Finished processing {filename}!")
    return f"Success: {filename} was fully processed."

@celery_app.task(name="tasks.ingest_file")
def process_ingest_file(file_id) -> str:
    """Ingest the stored file end to end and return the file id."""

    file = FILE_STORE.get(file_id)

    print(f"Starting processing for {file.file_name}...")

    ingestor : Ingestor = Ingestor.ingestor_map.get(file.extension,None)
    text,metadata = ingestor.extract_text(file)
    text_chunks = CHUNKER.split_text(text)
    file_id = FILE_STORE.store(file)
    VECTOR_STORE.add(text_chunks , [metadata]*len(text_chunks))


    print(f"Finished processing {file.file_name}!")