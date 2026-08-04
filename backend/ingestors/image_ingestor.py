from backend.ingestors.ingestor import IngestableFile, Ingestor
from rapidocr_onnxruntime import RapidOCR
import base64
import time
from openai import OpenAI, RateLimitError


def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode("utf-8")


class ImageOCRIngestor(Ingestor):
    def __init__(self, type="img", accepted_format=None, name="OCR", groq_key=None):
        super().__init__(type, accepted_format, name)
        self.engine = RapidOCR()
        self.client = None
        if groq_key:
            self.client = OpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
            )

    def extract_text(self, file):
        file.file_obj.seek(0)
        file_bytes = file.file_obj.read()
        result, elapse = self.engine(file_bytes)
        if result:
            text = " ".join([item[1] for item in result])
        else:
            text = ""
            
        return text, self.extract_metadata(file)

    def api_caption(self, file: IngestableFile):
        """Calls a groq model to generate image captions."""
        if not self.client:
            raise ValueError("API key not provided.")

        file.file_obj.seek(0)
        base64_image = encode_image(file.file_obj)
        try:
            response = self.client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """
                                    Describe this image in detail as if creating a searchable caption for it. Write 3-5 natural, flowing sentences that cover:

                                    - What the image shows overall (scene, setting, location type, indoor/outdoor, time of day, weather if visible)
                                    - Any people, animals, or objects present, including notable colors, brands, or distinguishing details
                                    - Any actions, activities, or events taking place
                                    - Any visible text, numbers, signs, or labels — transcribe them exactly as written
                                    - The overall mood, style, or context (e.g. candid photo, screenshot, document scan, receipt, artwork)

                                    Be specific and use concrete nouns and descriptive adjectives rather than vague language, since this description will be used for semantic search — someone should be able to find this image later by describing what's in it.

                                    Do not include any preamble, headers, labels, or formatting. Do not use JSON or markdown. Do not include phrases like "the image shows" or "this is a picture of" — start directly with the description itself.

                                    If the image is a document, receipt, or screenshot rather than a photo, prioritize transcribing all visible text accurately over describing visual style.
                            """,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                temperature=0.0,
                max_tokens=300,
                extra_body={
                    "reasoning_effort": "none",
                    "reasoning_format": "hidden",
                },
            )
            result = response.choices[0].message.content
            return result, self.extract_metadata(file)

        except RateLimitError as e:
            # Handles 429 errors gracefully if you scan multiple images too fast
            print("rate limit reached. Waiting 5 seconds before retry...")
            time.sleep(5)
            return self.api_caption(file)

