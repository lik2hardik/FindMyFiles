# CONFIG
##################################################################

from pathlib import Path
from backend.filestore.local_filestore import LocalSQLiteFileStore
from backend.ingestors.text_ingestor import TextIngestor
from backend.ingestors.image_ingestor import ImageOCRIngestor
from backend.ingestors.audio_ingestor import AudioIngestor
from backend.ingestors.pdf_ingestor import PdfIngestor
from backend.vector_store.local_vec_store import ChromaDBVectorStore
from backend.chunker.recursive_chunker import RecursiveChunker
from backend.app_state import AppState
import dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

dotenv.load_dotenv(dotenv_path=ENV_PATH, override=False)
GROQ_KEY = os.getenv("GROQ_KEY", "").strip() or None

TEXT_INGESTOR = TextIngestor(accepted_formats=["txt", "md"])
IMG_INGESTOR = ImageOCRIngestor(accepted_formats=["jpg", "png", "jpeg"], use_api=True)
AUDIO_INGESTOR = AudioIngestor(accepted_formats=["wav", "mp3"], use_api=False)
PDF_INGESTOR = PdfIngestor(accepted_formats=["pdf"])

CHUNKER = RecursiveChunker(chunk_size=512, overlap=64)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
VECSTORE_DIR = os.path.join(DATA_DIR, "vecstore")
FILESTORE_DIR = os.path.join(DATA_DIR, "filestore")

VECTOR_STORE = ChromaDBVectorStore(path=VECSTORE_DIR)

FILE_STORE = LocalSQLiteFileStore(path=FILESTORE_DIR)

APP_STATE_DIR = os.path.join(DATA_DIR, "app_state")
APP_STATE = AppState(APP_STATE_DIR)

##################################################################
