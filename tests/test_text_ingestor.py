import pytest
from backend.ingestors.text_ingestor import TextIngestor
from backend.filestore.filestore import IngestableFile
from backend.ingestors.ingestor import Metadata


@pytest.mark.asyncio
async def test_text_ingestor_extracts_valid_text(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")

    with open(test_file, "r") as f:
        ingestable = IngestableFile(f)
        ingestor = TextIngestor(accepted_format=["txt"])

        text, metadata = await ingestor.extract_text(ingestable)

    assert text == "Hello World"
    assert metadata.extension == "txt"
    assert metadata.type == "text"


@pytest.mark.asyncio
async def test_text_ingestor_outputs_valid_type(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")

    with open(test_file, "r") as f:
        ingestable = IngestableFile(f)
        ingestor = TextIngestor(accepted_format=["txt"])
        text, metadata = await ingestor.extract_text(ingestable)

    assert type(text) is str
    assert type(metadata) is Metadata


@pytest.mark.asyncio
async def test_text_ingestor_throws_type_error(tmp_path):
    test_file = tmp_path / "test.csv"
    test_file.write_text("Hello World")

    with pytest.raises(TypeError) as exc_info:
        with open(test_file, "rb") as f:
            ingestable = IngestableFile(f)
            ingestor = TextIngestor(accepted_format=["md"])
            await ingestor.extract_text(ingestable)

    assert "does not match any type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_text_ingestor_valid_multiple_accepted(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")

    with open(test_file, "rb") as f:
        ingestable = IngestableFile(f)
        ingestor = TextIngestor(accepted_format=["md", "txt"])
        text, metadata = await ingestor.extract_text(ingestable)

    assert text == "Hello World"
    assert metadata.extension == "txt"
