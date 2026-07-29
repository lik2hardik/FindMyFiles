from abc import abstractmethod, ABC
import io
from pathlib import Path


class IngestableFile:
    def __init__(self, file_obj: io.IOBase, name: str = None):
        """
        Accepts any file-like object passed from the application.
        """
        self.file_obj = file_obj
        self.file_name = name if name else getattr(file_obj, "name", "unknown_source")
        self.extension = Path(self.file_name).suffix[1:].lower() or "unknown"

    def get_file(self):
        return {
            "file_name": self.file_name,
            "extension": self.extension,
            "file": self.file_obj,
        }


class FileStore(ABC):
    def __init__(self, path: str = None):
        self.path = path

    @abstractmethod
    def get(self, id):
        "returns the file given the unique id of the file."
        pass

    @abstractmethod
    def store(self, file: IngestableFile) -> str:
        "stores file on the system and returns it's unique id"
