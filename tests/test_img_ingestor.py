from backend.ingestors.image_ingestor import ImageOCRIngestor
from backend.filestore.filestore import IngestableFile
import dotenv


def test_image_ingestor_extracts_valid_text():
    test_file = "/home/link2/Code/Projects/FindMyFiles/tests/stocks.jpg"
    ingestor = ImageOCRIngestor(accepted_format=["jpg","png"])


    with open(test_file, "rb") as f:
        ingestable = IngestableFile(f)
        result, metadata = ingestor.extract_text(ingestable)
        
        assert isinstance(result,str)
        assert result != ""
        assert "amex" in result.lower()


def test_image_ingestor_extracts_valid_text_api():
    test_file = "/home/link2/Code/Projects/FindMyFiles/tests/billboard.png"
    GROQ_KEY = dotenv.dotenv_values()["GROQ_KEY"]
    ingestor = ImageOCRIngestor(accepted_format=["jpg","png"],groq_key=GROQ_KEY)


    with open(test_file, "rb") as f:
        ingestable = IngestableFile(f)
        result,metadata = ingestor.api_caption(ingestable)

        assert isinstance(result,str)
        assert result != ""
        assert "billboard" in result.lower()
