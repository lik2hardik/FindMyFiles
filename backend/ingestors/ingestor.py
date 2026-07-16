from abc import abstractmethod
import io

class IngestableFile():
    def __init__(self, file_obj: io.IOBase):
        """
        Accepts any file-like object passed from the application.
        """
        self.file_obj = file_obj
        self.file_name = getattr(file_obj, 'name', 'unknown_source')
        self.extension = self.file_name.split('.')[-1].lower() if '.' in self.file_name else 'unknown'

    def get_file(self):
        return {
           "file_name" : self.file_name,
           "extension" : self.extension,
           "file": self.file_obj
        }
    
class Ingestor:
    def __init__(self, type=None, accepted_format=None, name="default"):
        self.name = name
        self.type = type
        self.accepted_format = accepted_format

    @abstractmethod
    async def extract_text(self, file:IngestableFile) -> str:
        """
        Given the media object, extract the relevant text.
        """
        pass
