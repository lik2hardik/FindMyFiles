from abc import abstractmethod, ABC
from backend.filestore.filestore import IngestableFile
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class Metadata(BaseModel):
    file_name: str
    type: str
    extension: str
    created_at_ts: float = Field(
        default_factory=lambda: datetime.now(timezone.utc).timestamp()
    )


class Ingestor(ABC):
    "Class to Ingest file into chunks and metadata."
    accepted_formats = [] # to store all accepted formats
    ingestor_map = {} # stores which format corrosponds to which ingestor

    def __init__(self, type=None, accepted_format=None, name="default"):
        self.name = name
        self.type = type
        self.accepted_format = accepted_format

        Ingestor.accepted_formats.extend(self.accepted_format)
        for format in self.accepted_format:
            Ingestor.ingestor_map[format] = self

    @abstractmethod
    def extract_text(self, file: IngestableFile) -> tuple[str, Metadata]:
        """
        Given the media object, extract the relevant text and metadata.
        """
        pass

    def extract_metadata(self, file: IngestableFile) -> Metadata:
        return Metadata(
            file_name=file.file_name, type=self.type, extension=file.extension
        )
