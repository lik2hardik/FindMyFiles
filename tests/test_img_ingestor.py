import os
from pathlib import Path

import pytest

from backend.filestore.filestore import IngestableFile
from backend.ingestors.image_ingestor import ImageOCRIngestor

TESTS_DIR = Path(__file__).resolve().parent


def test_image_ingestor_extracts_valid_text():
    test_file = TESTS_DIR / "stocks.jpg"
    ingestor = ImageOCRIngestor(accepted_format=["jpg", "png"], use_api=False)

    with open(test_file, "rb") as f:
        ingestable = IngestableFile(f)
        result, metadata = ingestor.extract_text(ingestable)

    assert isinstance(result, str)
    assert result != ""
    assert "amex" in result.lower()


def test_image_ingestor_extracts_valid_text_api():
    if not os.environ.get("GROQ_KEY"):
        pytest.skip("GROQ_KEY not set; skipping API caption test")

    test_file = TESTS_DIR / "billboard.png"
    ingestor = ImageOCRIngestor(accepted_format=["jpg", "png"], use_api=True)

    with open(test_file, "rb") as f:
        ingestable = IngestableFile(f)
        result, metadata = ingestor.api_caption(ingestable)

    assert isinstance(result, str)
    assert result != ""