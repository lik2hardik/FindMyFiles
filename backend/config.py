# CONFIG
##################################################################

from functools import lru_cache
from pathlib import Path
import dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

dotenv.load_dotenv(dotenv_path=ENV_PATH, override=False)
GROQ_KEY = os.getenv("GROQ_KEY", "").strip() or None

TEXT_INGESTOR = TextIngestor(accepted_format=["txt", "md"])
IMG_INGESTOR = ImageOCRIngestor(accepted_format=["jpg", "png", "jpeg"],use_api=True)
AUDIO_INGESTOR = AudioIngestor(accepted_format=["wav","mp3"],use_api=False)

CHUNKER = RecursiveChunker(chunk_size=512, overlap=64)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
VECSTORE_DIR = os.path.join(DATA_DIR, "vecstore")
FILESTORE_DIR = os.path.join(DATA_DIR, "filestore")
APP_STATE_DIR = os.path.join(DATA_DIR, "app_state")


@lru_cache(maxsize=1)
def get_text_ingestor():
    from backend.ingestors.text_ingestor import TextIngestor

    return TextIngestor(accepted_format=["txt", "md"])


@lru_cache(maxsize=1)
def get_img_ingestor():
    from backend.ingestors.image_ingestor import ImageOCRIngestor

    return ImageOCRIngestor(accepted_format=["jpg", "png", "jpeg"], use_api=True)


@lru_cache(maxsize=1)
def get_audio_ingestor():
    from backend.ingestors.audio_ingestor import AudioIngestor

    return AudioIngestor(accepted_format=["wav", "mp3"], use_api=False)


@lru_cache(maxsize=1)
def get_chunker():
    from backend.chunker.recursive_chunker import RecursiveChunker

    return RecursiveChunker(chunk_size=512, overlap=64)


@lru_cache(maxsize=1)
def get_vector_store():
    from backend.vector_store.local_vec_store import ChromaDBVectorStore

    return ChromaDBVectorStore(path=VECSTORE_DIR)


@lru_cache(maxsize=1)
def get_file_store():
    from backend.filestore.local_filestore import LocalSQLiteFileStore

    return LocalSQLiteFileStore(path=FILESTORE_DIR)


@lru_cache(maxsize=1)
def get_app_state():
    from backend.app_state import AppState

    return AppState(APP_STATE_DIR)

##################################################################