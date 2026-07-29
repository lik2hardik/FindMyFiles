import time
from celery_app import celery_app

@celery_app.task(name="tasks.process_file_task")
def process_file_task(filename: str) -> str:
    """Simulates a heavy file processing task."""
    print(f"Starting processing for {filename}...")
    time.sleep(5)  # Simulate expensive work
    print(f"Finished processing {filename}!")
    return f"Success: {filename} was fully processed."
