from functools import lru_cache
from rapidocr_onnxruntime import RapidOCR
from backend.ingestors.base_ingestor import IngestionError


@lru_cache(maxsize=1)
def get_ocr_engine():
    return RapidOCR()


def ocr_bytes(image_bytes: bytes) -> str:
    try:
        result, _ = get_ocr_engine()(image_bytes)
        return " ".join(item[1] for item in result) if result else ""
    except Exception as e:
        raise IngestionError(f"Failed to OCR bytes: {str(e)}") from e
