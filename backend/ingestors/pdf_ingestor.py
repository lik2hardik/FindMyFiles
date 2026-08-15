import pymupdf

from backend.ingestors.ingestor import IngestFailed, Ingestor
from backend.ingestors.ocr_utils import ocr_bytes


class PdfIngestor(Ingestor):
    def __init__(self, type="pdf", accepted_format=None, name="PDF"):
        super().__init__(type, accepted_format, name)

    def extract_text(self, file):
        file.file_obj.seek(0)
        data = file.file_obj.read()
        if isinstance(data, str):
            data = data.encode("utf-8")

        try:
            with pymupdf.open(stream=data, filetype="pdf") as doc:
                page_texts = []
                for page_num, page in enumerate(doc, start=1):
                    text = page.get_text().strip()
                    if not text:
                        pix = page.get_pixmap(dpi=200)
                        text = ocr_bytes(pix.tobytes("png")).strip()
                    if text:
                        page_texts.append(f"[Page {page_num}]\n{text}")
        except Exception as e:
            raise IngestFailed(f"PDF {file.file_name} could not be parsed: {e}") from e

        text = "\n\n".join(page_texts).strip()
        if not text:
            raise IngestFailed(
                f"PDF {file.file_name} produced no text via extraction or OCR."
            )

        return text, self.extract_metadata(file)
