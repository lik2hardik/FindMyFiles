from backend.ingestors.image_ingestor import ImageOCRIngestor
from backend.filestore.filestore import IngestableFile
import os


def test_image_ingestor_extracts_valid_text():
    cwd = os.getcwd()
    test_file = os.path.join(cwd, "tests/stocks.jpg")
    ingestor = ImageOCRIngestor(accepted_format=["jpg", "png"])

    with open(test_file, "rb") as f:
        ingestable = IngestableFile(f)
        result, metadata = ingestor.extract_text(ingestable)

        assert isinstance(result, str)
        assert result != ""
        assert "amex" in result.lower()


def test_image_ingestor_extracts_valid_text_api():
    cwd = os.getcwd()
    test_file = os.path.join(cwd, "tests/billboard.png")
    ingestor = ImageOCRIngestor(accepted_format=["jpg", "png"])

    with open(test_file, "rb") as f:
        ingestable = IngestableFile(f)
        result, metadata = ingestor.extract_text(ingestable)

        assert isinstance(result, str)
        assert result != ""
        assert "billboard" in result.lower()
