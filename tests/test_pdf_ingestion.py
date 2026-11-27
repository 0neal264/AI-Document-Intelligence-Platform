"""Tests for the standalone PDF ingestion engine using generated PDFs."""

from io import BytesIO

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from documind.ingestion import (
    EncryptedPDFError,
    ExtractionStatus,
    InvalidPDFError,
    InvalidPDFTypeError,
    UploadTooLargeError,
    ingest_pdf,
)


def make_pdf(*page_texts: str, metadata: dict[str, str] | None = None) -> bytes:
    writer = PdfWriter()
    for text in page_texts:
        page = writer.add_blank_page(width=300, height=300)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
                NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject(
                    {NameObject("/F1"): writer._add_object(font)}
                )
            }
        )
        stream = DecodedStreamObject()
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream.set_data(f"BT /F1 12 Tf 20 200 Td ({escaped}) Tj ET".encode())
        page[NameObject("/Contents")] = writer._add_object(stream)
    if metadata:
        writer.add_metadata(metadata)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.fixture
def multi_page_pdf() -> bytes:
    return make_pdf(
        "First page text", "Second page text", metadata={"/Title": "Sample"}
    )


def test_ingests_text_page_by_page_and_preserves_metadata(multi_page_pdf):
    result = ingest_pdf(multi_page_pdf, "sample.pdf")

    assert result.filename == "sample.pdf"
    assert result.document_id
    assert result.page_count == 2
    assert result.metadata["Title"] == "Sample"
    assert [page.page_number for page in result.pages] == [1, 2]
    assert [page.extracted_text.strip() for page in result.pages] == [
        "First page text",
        "Second page text",
    ]
    assert all(
        page.extraction_status is ExtractionStatus.EXTRACTED for page in result.pages
    )


def test_empty_pdf_has_zero_pages():
    writer = PdfWriter()
    output = BytesIO()
    writer.write(output)

    result = ingest_pdf(output.getvalue(), "empty.pdf")

    assert result.page_count == 0
    assert result.pages == ()


def test_blank_page_is_returned_with_empty_status():
    result = ingest_pdf(make_pdf(""), "blank.pdf")

    assert result.pages[0].page_number == 1
    assert result.pages[0].extracted_text == ""
    assert result.pages[0].extraction_status is ExtractionStatus.EMPTY


def test_rejects_invalid_extension():
    with pytest.raises(InvalidPDFTypeError, match="extension"):
        ingest_pdf(b"%PDF-1.4", "document.txt")


def test_rejects_non_pdf_content():
    with pytest.raises(InvalidPDFTypeError, match="signature"):
        ingest_pdf(b"not a pdf", "document.pdf")


def test_rejects_upload_over_configured_size(multi_page_pdf):
    with pytest.raises(UploadTooLargeError, match="limit"):
        ingest_pdf(multi_page_pdf, "large.pdf", max_upload_bytes=10)


def test_rejects_corrupted_pdf():
    with pytest.raises(InvalidPDFError, match="Could not read PDF"):
        ingest_pdf(b"%PDF-1.4\\nnot a valid PDF", "corrupt.pdf")


def test_rejects_encrypted_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    writer.encrypt("secret")
    output = BytesIO()
    writer.write(output)

    with pytest.raises(EncryptedPDFError, match="Encrypted"):
        ingest_pdf(output.getvalue(), "encrypted.pdf")


def test_failed_page_extraction_is_explicit(monkeypatch):
    from pypdf._page import PageObject

    def fail_extract(self, *args, **kwargs):
        raise RuntimeError("cannot decode page")

    monkeypatch.setattr(PageObject, "extract_text", fail_extract)
    result = ingest_pdf(make_pdf("text"), "failed-page.pdf")

    assert result.page_count == 1
    assert result.pages[0].extraction_status is ExtractionStatus.FAILED
    assert "cannot decode page" in result.pages[0].error
