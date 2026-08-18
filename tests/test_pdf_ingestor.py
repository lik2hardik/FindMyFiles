import io

import pymupdf
import pytest

from backend.filestore.base_filestore import IngestableFile
from backend.ingestors.base_ingestor import IngestFailed, Ingestor, Metadata
from backend.ingestors.pdf_ingestor import PdfIngestor


def make_text_pdf(path, pages):
    doc = pymupdf.open()
    for content in pages:
        page = doc.new_page()
        page.insert_text((72, 72), content)
    doc.save(path)
    doc.close()


def make_image_pdf(path, num_pages=1):
    doc = pymupdf.open()
    for _ in range(num_pages):
        page = doc.new_page()
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 100), False)
        page.insert_image(page.rect, stream=pix.tobytes("png"))
    doc.save(path)
    doc.close()


@pytest.fixture
def ingestor():
    return PdfIngestor(accepted_format=["pdf"])


def test_pdf_registration(ingestor):
    assert "pdf" in Ingestor.accepted_formats
    assert Ingestor.ingestor_map["pdf"] is ingestor


def test_text_pdf_extracts_all_pages_with_markers(tmp_path, ingestor):
    pdf_path = tmp_path / "sample.pdf"
    make_text_pdf(pdf_path, ["Hello from page one", "Second page content"])

    with open(pdf_path, "rb") as f:
        ingestable = IngestableFile(f)
        text, metadata = ingestor.extract_text(ingestable)

    assert "[Page 1]" in text
    assert "[Page 2]" in text
    assert "Hello from page one" in text
    assert "Second page content" in text


def test_text_pdf_returns_valid_types(tmp_path, ingestor):
    pdf_path = tmp_path / "sample.pdf"
    make_text_pdf(pdf_path, ["content"])

    with open(pdf_path, "rb") as f:
        ingestable = IngestableFile(f)
        text, metadata = ingestor.extract_text(ingestable)

    assert type(text) is str
    assert type(metadata) is Metadata


def test_pdf_metadata_correct(tmp_path, ingestor):
    pdf_path = tmp_path / "docs.pdf"
    make_text_pdf(pdf_path, ["content"])

    with open(pdf_path, "rb") as f:
        ingestable = IngestableFile(f, "docs.pdf")
        text, metadata = ingestor.extract_text(ingestable)

    assert metadata.file_name == "docs.pdf"
    assert metadata.extension == "pdf"
    assert metadata.type == "pdf"


def test_scanned_pdf_uses_ocr(tmp_path, ingestor, monkeypatch):
    pdf_path = tmp_path / "scan.pdf"
    make_image_pdf(pdf_path)
    monkeypatch.setattr(
        "backend.ingestors.pdf_ingestor.ocr_bytes", lambda b: "scanned ocr text"
    )

    with open(pdf_path, "rb") as f:
        ingestable = IngestableFile(f)
        text, metadata = ingestor.extract_text(ingestable)

    assert "[Page 1]" in text
    assert "scanned ocr text" in text


def test_mixed_text_and_scanned_pages(tmp_path, ingestor, monkeypatch):
    pdf_path = tmp_path / "mixed.pdf"
    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text((72, 72), "digital text page")
    page2 = doc.new_page()
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 100), False)
    page2.insert_image(page2.rect, stream=pix.tobytes("png"))
    doc.save(pdf_path)
    doc.close()
    monkeypatch.setattr(
        "backend.ingestors.pdf_ingestor.ocr_bytes", lambda b: "image page ocr"
    )

    with open(pdf_path, "rb") as f:
        ingestable = IngestableFile(f)
        text, metadata = ingestor.extract_text(ingestable)

    assert "digital text page" in text
    assert "image page ocr" in text


def test_corrupt_pdf_raises_ingest_failed(tmp_path, ingestor):
    pdf_path = tmp_path / "broken.pdf"
    pdf_path.write_bytes(b"this is not a pdf at all")

    with open(pdf_path, "rb") as f:
        ingestable = IngestableFile(f)
        with pytest.raises(IngestFailed):
            ingestor.extract_text(ingestable)


def test_empty_pdf_raises_ingest_failed(tmp_path, ingestor, monkeypatch):
    pdf_path = tmp_path / "empty.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(pdf_path)
    doc.close()
    monkeypatch.setattr("backend.ingestors.pdf_ingestor.ocr_bytes", lambda b: "")

    with open(pdf_path, "rb") as f:
        ingestable = IngestableFile(f)
        with pytest.raises(IngestFailed):
            ingestor.extract_text(ingestable)


def test_scanned_pdf_without_ocr_result_raises(tmp_path, ingestor, monkeypatch):
    pdf_path = tmp_path / "noscantext.pdf"
    make_image_pdf(pdf_path)
    monkeypatch.setattr("backend.ingestors.pdf_ingestor.ocr_bytes", lambda b: "")

    with open(pdf_path, "rb") as f:
        ingestable = IngestableFile(f)
        with pytest.raises(IngestFailed):
            ingestor.extract_text(ingestable)


def test_ingestor_accepts_bytes_io(ingestor):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "from buffer")
    buffer = io.BytesIO(doc.tobytes())
    doc.close()

    ingestable = IngestableFile(buffer, "buffer.pdf")
    text, metadata = ingestor.extract_text(ingestable)

    assert "from buffer" in text
