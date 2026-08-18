from .base_ingestor import BaseIngestor, IngestionError, IngestableFile


class TextIngestor(BaseIngestor):
    def __init__(
        self, type="text", accepted_formats: list[str] = None, name="default text"
    ):
        try:
            super().__init__(type, accepted_formats, name)
        except IngestionError as e:
            raise e
        except Exception as e:
            raise IngestionError(f"Failed to initialize TextIngestor: {e}") from e

    def extract_text(self, file: IngestableFile):

        if file.extension not in self.accepted_formats:
            raise IngestionError(
                f"{file.extension} does not match any type in {self.accepted_formats}"
            )
        try:
            file.file_obj.seek(0)
            data = file.file_obj.read()
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="ignore")
            return data, self.extract_metadata(file)
        except IngestionError as e:
            raise e
        except Exception as e:
            raise IngestionError(f"Failed to extract text: {e}") from e
