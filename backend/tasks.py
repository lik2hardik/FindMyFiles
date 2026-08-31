from re import A
import time

from sqlalchemy.engine.result import exc
from backend.celery_app import celery_app
from backend.ingestors.base_ingestor import BaseIngestor, IngestionError
from backend.config import CHUNKER, FILE_STORE, VECTOR_STORE, APP_STATE
from backend.app_state import AppStateError


@celery_app.task(name="tasks.ingest_file")
def process_ingest_file(file_id, app_state_id) -> str:
    """Ingest the stored file end to end and return the file id."""

    try:
        file = FILE_STORE.get(file_id)
        print(f"Starting processing for {file.file_name}...")

        ingestor: BaseIngestor | None = BaseIngestor.ingestor_map.get(file.extension, None)

        if ingestor is None:
            raise IngestionError(f"No ingestor found for file type: {file.extension}")

        text, metadata = ingestor.extract_text(file)
        if not text or not text.strip():
            raise IngestionError(f"No text could be extracted from {file.file_name} ")
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


    except IngestionError as e:
        try:
            APP_STATE.update_file(
                app_state_id, status="Ingestion Failed", error_msg=f"Ingestion Error: {e}"
            )
        except AppStateError as app_state_e:
            return f"AppState Error: {app_state_e}"

        return f"Ingestion Error: {e}"

    except AppStateError as e:
        try:
            APP_STATE.update_file(
                app_state_id, status="Ingestion Failed", error_msg=f"AppState Error: {e}"
            )
        except AppStateError as app_state_e:
            return f"AppState Error: {app_state_e}"
        return f"AppState Error: {e}"

    except Exception as e:
        try:
            APP_STATE.update_file(
                app_state_id,
                status="Ingestion Failed",
                error_msg=f"Unexpected error during ingestion: {e}",
            )
        except AppStateError as app_state_e:
            return f"AppState Error: {app_state_e}"
        return f"Unexpected error: {e}"
