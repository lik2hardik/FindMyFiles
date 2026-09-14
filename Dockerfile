# =============================================================================
# FindMyFiles Dockerfile - Multi-stage build for lightweight production images
# =============================================================================
# This Dockerfile builds the entire application (backend + frontend) and can be
# used for both the API server and Celery worker by changing the CMD.
#
# Build: docker build -t findmyfiles .
# Run API: docker run -p 8000:8000 findmyfiles
# Run Worker: docker run findmyfiles celery -A backend.celery_app worker
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and prepare the application
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first (layer caching optimization)
# Changes to dependencies require rebuild, but code changes don't
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev dependencies for production)
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY backend/ backend/
COPY frontend/ frontend/

# Install the project itself (without dev dependencies)
RUN uv sync --frozen --no-dev

# ---------------------------------------------------------------------------
# Stage 2: Runtime - Minimal image for production
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Install runtime dependencies:
# - libgl1 and libglib2.0-0: OpenCV dependencies for image processing
# - ffmpeg: Audio processing for Whisper
# - tesseract-ocr: OCR engine for text extraction from images
# - libmagic1: File type detection
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        ffmpeg \
        tesseract-ocr \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code from builder
COPY --from=builder /app/backend /app/backend
COPY --from=builder /app/frontend /app/frontend

# Set working directory
WORKDIR /app

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create data directory for mounted volumes
RUN mkdir -p /app/backend/data/app_state \
    /app/backend/data/filestore \
    /app/backend/data/vecstore

# Expose ports
# 8000: FastAPI backend
# 7860: Gradio frontend (when running frontend service)
EXPOSE 8000 7860

# Health check for the API server
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Default command: Run the FastAPI backend
# Override with: docker run findmyfiles celery -A backend.celery_app worker
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
