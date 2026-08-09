# FindMyFiles
Multimodal RAG based application that helps you find and query your files with natural language queries.

`sudo systemctl stop redis-server && redis-server`

`celery -A backend.celery_app.celery_app worker --loglevel=info`

`uv run task dev`

`chroma run --path backend/data/vecstore --host localhost --port 8001`

`gradio frontend/app.py`