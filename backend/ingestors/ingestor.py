from abc import abstractmethod, ABC
from backend.filestore.filestore import IngestableFile
from pydantic import BaseModel,Field
from datetime import datetime, timezone

class Metadata(BaseModel):
    file_name: str 
    type: str
    extension: str
    created_at_ts: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())

class Ingestor(ABC):
    "Class to Ingest file into chunks and metadata."
    def __init__(self, type=None, accepted_format=None, name="default"):
        self.name = name
        self.type = type
        self.accepted_format = accepted_format

    @abstractmethod
    async def extract_text(self, file: IngestableFile) -> str:
        """
        Given the media object, extract the relevant text.
        """
        pass
    
    def extract_metadata(self, file: IngestableFile) -> Metadata:
        return Metadata(
            file_name= file.file_name,
            type = self.type,
            extension = file.extension
        )
