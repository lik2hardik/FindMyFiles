from functools import lru_cache
from rapidocr_onnxruntime import RapidOCR


@lru_cache(maxsize=1)
def get_ocr_engine():
    return RapidOCR()


def ocr_bytes(image_bytes: bytes) -> str:
    result, _ = get_ocr_engine()(image_bytes)
    return " ".join(item[1] for item in result) if result else ""
