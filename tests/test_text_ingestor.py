import pytest
from backend.ingestors.text_ingestor import TextIngestor
from backend.ingestors.ingestor import IngestableFile # Fix typo to 'ingestor' if needed

@pytest.mark.asyncio
async def test_text_ingestor_extracts_valid_text(tmp_path):
    # Create a temporary file safely using pytest fixtures
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")
    
    with open(test_file, "r") as f:
        # Mock or use your IngestableFile here
        ingestable = IngestableFile(f) 
        ingestor = TextIngestor()
        result = await ingestor.extract_text(ingestable)
        
    assert result == "Hello World"

async def test_text_ingestor_outputs_valid_type(tmp_path):
    # Create a temporary file safely using pytest fixtures
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")
    
    with open(test_file, "r") as f:
        # Mock or use your IngestableFile here
        ingestable = IngestableFile(f) 
        ingestor = TextIngestor()
        result = await ingestor.extract_text(ingestable)
        
    assert type(result) is str

@pytest.mark.asyncio
async def test_text_ingestor_throws_type_error(tmp_path):
    test_file = tmp_path / "test.csv"
    test_file.write_text("Hello World")
    
    with pytest.raises(TypeError) as exc_info:
        with open(test_file, "r") as f:
            ingestable = IngestableFile(f) 
            ingestor = TextIngestor()
            # This line should trigger the TypeError
            await ingestor.extract_text(ingestable)
            
    # Verify the error message matches
    assert "does not match any type" in str(exc_info.value)

@pytest.mark.asyncio
async def test_text_ingestor_valid_multiple_accepted(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")

    with open(test_file, "r") as f:
        ingestable = IngestableFile(f) 
        ingestor = TextIngestor(accepted_format=["md",'txt'])
        result = await ingestor.extract_text(ingestable)

    assert result == "Hello World"
