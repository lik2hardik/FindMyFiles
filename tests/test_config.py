import subprocess
import sys
from pathlib import Path

import pytest

from backend import config


def test_config_loads_groq_key_from_dotenv_file():
    if not config.GROQ_KEY:
        pytest.skip("GROQ_KEY not set in .env; skipping key check")
    assert isinstance(config.GROQ_KEY, str)
    assert config.GROQ_KEY.startswith("gsk_")


HEAVY_MODULES = [
    "rapidocr_onnxruntime",
    "chromadb",
    "sqlmodel",
    "openai",
    "faster_whisper",
]


def test_importing_config_is_lazy():
    # Runs in a fresh interpreter because in-process imports would be cached
    # by earlier tests. Heavy deps must NOT be loaded by `import backend.config`.
    probe = (
        "import sys; import backend.config; "
        "heavy = any(m in sys.modules for m in "
        f"{HEAVY_MODULES!r}); "
        "print('heavy' if heavy else 'clean')"
    )
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd=str(project_root),
    )
    assert result.stdout.strip() == "clean", result.stderr


def test_accessors_return_cached_singletons():
    assert config.get_chunker() is config.get_chunker()
    assert config.get_text_ingestor() is config.get_text_ingestor()
    assert config.get_audio_ingestor() is config.get_audio_ingestor()
    assert config.get_file_store() is config.get_file_store()
    assert config.get_app_state() is config.get_app_state()
    assert config.get_vector_store() is config.get_vector_store()


def test_text_ingestor_exposes_accepted_formats():
    assert config.get_text_ingestor().accepted_format == ["txt", "md"]