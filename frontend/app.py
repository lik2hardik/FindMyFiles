import gradio as gr
import os
import time
import requests

BACKEND_URL = os.getenv("FINDMYFILES_BACKEND_URL", "http://127.0.0.1:8000")

REQUEST_TIMEOUT = (10, 300)
POLL_INTERVAL_SECONDS = 1.0
POLL_TIMEOUT_SECONDS = 600

STATUS_ORDER = [
    "Storage Complete",
    "Ingestion Complete",
    "Chunking Complete",
    "Embedding Complete",
    "Ingestion Successful",
    "Ingestion Failed",
]
TERMINAL_STATUSES = {"Ingestion Successful", "Ingestion Failed"}


def get_formats():
    try:
        response = requests.get(f"{BACKEND_URL}/formats", timeout=(5, 15))
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


def extract_error(response):
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict) and payload.get("detail"):
        return str(payload["detail"])
    return f"HTTP {response.status_code}"


def status_text(row):
    status = row.get("status", "unknown")
    lines = [f"Status: {status}"]
    if status == "Ingestion Failed":
        lines.append(f"Failure reason: {row.get('error_message') or 'Unknown'}")
    return "\n".join(lines)


def render_formats(formats):
    if not formats:
        return "Could not load supported formats from the backend (is it running?)."
    return "Supported formats: " + ", ".join(formats)


def upload_file(file_path):
    with open(file_path, "rb") as f:
        response = requests.post(
            url=f"{BACKEND_URL}/upload/",
            files={
                "file": (os.path.basename(file_path), f, "application/octet-stream")
            },
            timeout=REQUEST_TIMEOUT,
        )
    return response


def poll_file_status(app_state_id, progress):
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    seen = set()
    while time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_SECONDS)
        try:
            response = requests.get(
                f"{BACKEND_URL}/files/{app_state_id}", timeout=(5, 15)
            )
        except requests.RequestException as e:
            yield f"Error: failed to reach backend while polling: {e}"
            return
        if response.status_code == 404:
            yield (
                f"Error: no status entry found for this upload "
                f"(`/files/{app_state_id}` returned 404)."
            )
            return
        if response.status_code != 200:
            yield f"Error: status request failed: {extract_error(response)}"
            return

        row = response.json()
        status = row.get("status", "unknown")

        if status in STATUS_ORDER and status not in seen:
            seen.add(status)
            fraction = STATUS_ORDER.index(status) / (len(STATUS_ORDER) - 1)
            progress(fraction, desc=status)

        yield status_text(row)

        if status in TERMINAL_STATUSES:
            return

    yield (
        f"Timeout: status did not reach a terminal state after "
        f"{POLL_TIMEOUT_SECONDS}s. Check the worker queue."
    )


def ingest_file(file_path, progress=gr.Progress()):  # noqa: B008
    if not file_path:
        return "Error: no file selected.", None

    file_name = os.path.basename(file_path)
    extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    supported = get_formats()
    if supported and extension not in supported:
        return (
            f"Error: `{extension or '(no extension)'}` is not a supported format. "
            f"Supported: {', '.join(supported)}",
            None,
        )

    try:
        response = upload_file(file_path)
    except requests.RequestException as e:
        return f"Error: upload failed: {e}", None

    if response.status_code != 200:
        return f"Error: upload failed: {extract_error(response)}", None

    try:
        job = response.json()
    except ValueError:
        return "Error: unexpected response from backend.", None

    if "app_state_id" not in job:
        formats = job.get("acceptable_formats") or supported
        return (
            f"Error: `{extension or '(no extension)'}` is not a supported format. "
            f"Supported: {', '.join(formats)}",
            None,
        )

    app_state_id = job["app_state_id"]

    for item in poll_file_status(app_state_id, progress):
        yield item, job


def build_ingest_tab():
    with gr.Tab("Ingest"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown(
                    "## Ingest a file\n"
                    "Upload a file to the backend. It is stored immediately, then "
                    "asynchronously extracted, chunked and embedded by the worker pool."
                )
                gr.Markdown(value=render_formats(get_formats()))
                file_input = gr.File(label="File to ingest", type="filepath")
                upload_button = gr.Button("Upload & Ingest", variant="primary")
            with gr.Column(scale=1):
                status_box = gr.Textbox(
                    label="Ingestion Status", interactive=False, lines=3
                )
                details_box = gr.JSON(label="Job Response")
        upload_button.click(
            ingest_file,
            inputs=[file_input],
            outputs=[status_box, details_box],
        )


with gr.Blocks(title="FindMyFiles") as demo:
    build_ingest_tab()

if __name__ == "__main__":
    demo.launch(server_port=7860)
