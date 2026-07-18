from abc import abstractmethod, ABC
from backend.filestore.filestore import IngestableFile


class Ingestor(ABC):
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
