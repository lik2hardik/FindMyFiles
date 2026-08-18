from .base_ingestor import BaseIngestor, IngestableFile, IngestionError
from dotenv import load_dotenv
from openai import OpenAI
from faster_whisper import WhisperModel
import os
from functools import cached_property

load_dotenv()

GROQ_KEY = os.environ.get("GROQ_KEY")


class AudioIngestor(BaseIngestor):
    @cached_property
    def whisper(self):
        try:
            return WhisperModel("base", device="cpu", compute_type="int8")
        except Exception as e:
            raise IngestionError(f"Failed to initialize WhisperModel: {e}") from e

    def __init__(
        self,
        type="audio",
        accepted_formats: list[str] = None,
        name="default text",
        use_api=True,
    ):
        try:
            super().__init__(type, accepted_formats, name)
        except IngestionError as e:
            raise e
        except Exception as e:
            raise IngestionError(f"Failed to initialize AudioIngestor: {e}") from e

        self.client = None
        self.use_api = use_api

        if use_api:
            if not GROQ_KEY:
                raise IngestionError("GROQ_KEY environment variable not set")
            self.client = OpenAI(
                api_key=GROQ_KEY,
                base_url="https://api.groq.com/openai/v1",
            )

    def extract_text(self, file: IngestableFile):
        try:
            file.file_obj.seek(0)

            if not self.accepted_formats or file.extension not in self.accepted_formats:
                raise IngestionError(
                    f"{file.extension} does not match any type in {self.accepted_formats}"
                )

            if self.use_api:
                return self.extract_text_api(file), self.extract_metadata(file)

            return self.extract_text_local(file), self.extract_metadata(file)

        except IngestionError as e:
            raise e
        except Exception as e:
            raise IngestionError(f"Failed to extract text: {e}") from e

    def extract_text_local(self, file: IngestableFile):
        try:
            file.file_obj.seek(0)
            segments, info = self.whisper.transcribe(file.file_obj)
            return " ".join(seg.text for seg in segments)
        except IngestionError as e:
            raise e
        except Exception as e:
            raise IngestionError(f"Failed to extract text: {e}") from e

    def extract_text_api(self, file: IngestableFile):
        try:
            file.file_obj.seek(0)
            transcription = self.client.audio.transcriptions.create(
                file=(file.file_name, file.file_obj),
                model="whisper-large-v3-turbo",
                response_format="text",
            )
            return transcription
        except IngestionError as e:
            raise e
        except Exception as e:
            raise IngestionError(f"Failed to extract text: {e}") from e
