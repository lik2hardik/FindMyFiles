import gradio as gr
import os
import requests

BACKEND_URL = "http://127.0.0.1:8000"


def upload_file(file):
    get_file_url = f"{BACKEND_URL}/upload/"
    with open(file, "rb") as f:
        response = requests.post(
            url=get_file_url,
            files={"file": (os.path.basename(file), f, "application/octet-stream")},
        )
    return response.json()


def get_file(query):
    get_file_url = f"{BACKEND_URL}/get/"
    response = requests.get(url=get_file_url, params={"q": query})

    return response.json()


ingest = gr.Interface(
    fn=upload_file, inputs=["file"], outputs=["json"], api_name="ingest"
)

retrieval = gr.Interface(
    fn=get_file, inputs=["text"], outputs=["json"], api_name="retrieve"
)

demo = gr.TabbedInterface([ingest, retrieval], ["Upload", "Retrieve"])

if __name__ == "__main__":
    demo.launch(server_port=7860)
