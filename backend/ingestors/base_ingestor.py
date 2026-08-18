from abc import abstractmethod, ABC
from backend.filestore.base_filestore import IngestableFile
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class Metadata(BaseModel):
    file_name: str
    type: str
    extension: str
    created_at_ts: float = Field(
        default_factory=lambda: datetime.now(timezone.utc).timestamp()
    )

class IngestionError(Exception):
    "Generic Ingestion Error when extracting text from a file failed."
    pass


class BaseIngestor(ABC):
    "Class to Ingest file into chunks and metadata."


    all_formats = set()  # to store all accepted formats
    ingestor_map = dict()  # stores which format corrosponds to which ingestor

    def __init__(self, type=None, accepted_format=None, name="default"):
        self.name = name
        self.type = type
        self.accepted_formats = accepted_format
        self.update_ingestor_map()  # register this ingestor with the format map (used by child classes)

    def update_ingestor_map(self):
        for format in self.accepted_formats:
            if format in BaseIngestor.all_formats:
                raise IngestorError(f"Format {format} is already registered by {BaseIngestor.ingestor_map[format].name}.")

        for format in self.accepted_formats:
            BaseIngestor.all_formats.add(format)
            BaseIngestor.ingestor_map[format] = self


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
