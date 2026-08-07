from .ingestor import Ingestor, IngestableFile
from dotenv import load_dotenv
from openai import OpenAI
from faster_whisper import WhisperModel
import os

load_dotenv()

GROQ_KEY = os.environ.get("GROQ_KEY")

class AudioIngestor(Ingestor):
    def __init__(
        self, type="text", accepted_format: list[str] = None, name="default text",
        use_api=True
    ):
        super().__init__(type, accepted_format, name)

        self._whisper = None
        self.client = None
        self.use_api = use_api

        if use_api:
            if not GROQ_KEY:
                raise ValueError("GROQ_KEY environment variable not set")
            self.client = OpenAI(
                api_key=GROQ_KEY,
                base_url="https://api.groq.com/openai/v1",
            )

    @property
    def whisper(self):
        if self._whisper is None:
            self._whisper = WhisperModel("base", device="cpu", compute_type="int8")
        return self._whisper

    

    def extract_text(self, file: IngestableFile):
        file.file_obj.seek(0)

        if not self.accepted_format or file.extension not in self.accepted_format:
            raise TypeError(
                f"{file.extension} does not match any type in {self.accepted_format}"
    )

        if self.use_api:
            return self.extract_text_api(file), self.extract_metadata(file)

        return self.extract_text_local(file), self.extract_metadata(file)


    def extract_text_local(self, file:IngestableFile):
        file.file_obj.seek(0)
        segments, info = self.whisper.transcribe(file.file_obj)
        return " ".join(seg.text for seg in segments)

    def extract_text_api(self,file:IngestableFile):
        file.file_obj.seek(0)
        transcription = self.client.audio.transcriptions.create(
            file=(file.file_name , file.file_obj),        
            model="whisper-large-v3-turbo",
            response_format="text",
        )
        return transcription
